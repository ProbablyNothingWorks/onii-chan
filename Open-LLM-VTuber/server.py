import os
import re
import shutil
import atexit
import json
import asyncio
from typing import List, Dict, Any, Optional
import yaml
import numpy as np
from fastapi import FastAPI, WebSocket, APIRouter, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
from main import OpenLLMVTuberMain
from live2d_model import Live2dModel
from tts.stream_audio import AudioPayloadPreparer
import chardet
from loguru import logger
from pubsub_client import PubSubClient  # Your pubsub implementation
import uuid
from web3 import Web3  # For EVM interactions
from datetime import datetime


class WebSocketServer:
    """
    WebSocketServer initializes a FastAPI application with WebSocket endpoints and a broadcast endpoint.

    Attributes:
        config (dict): Configuration dictionary.
        app (FastAPI): FastAPI application instance.
        router (APIRouter): APIRouter instance for routing.
        connected_clients (List[WebSocket]): List of connected WebSocket clients for "/client-ws".
        server_ws_clients (List[WebSocket]): List of connected WebSocket clients for "/server-ws".
    """

    def __init__(self, open_llm_vtuber_main_config: Dict | None = None):
        """
        Initializes the WebSocketServer with the given configuration.
        """
        self.app = FastAPI()
        self.router = APIRouter()
        self.new_connected_clients: List[WebSocket] = []
        self.connected_clients: List[WebSocket] = []
        self.server_ws_clients: List[WebSocket] = []
        self.open_llm_vtuber_main_config: Dict | None = open_llm_vtuber_main_config
        self.active_sessions: Dict[str, OpenLLMVTuberMain] = {}
        
        # Initialize Pub/Sub client with Google Cloud settings
        pubsub_config = open_llm_vtuber_main_config.get("PUBSUB", {})
        self.pubsub = PubSubClient(
            project_id=pubsub_config.get("PROJECT_ID"),
            subscription_id=pubsub_config.get("SUBSCRIPTION_ID")
        )
        
        self.background_tasks = BackgroundTasks()
        
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(open_llm_vtuber_main_config.get("WEB3_RPC_URL")))
        self.nft_contract = self.init_nft_contract()
        
        # Register WebSocket endpoint
        self.app.websocket("/client-ws")(self.websocket_endpoint)
        
        # Start pubsub listener
        asyncio.create_task(self.listen_to_pubsub())
        
        self._setup_routes()
        self._mount_static_files()
        self.app.include_router(self.router)

    async def listen_to_pubsub(self):
        """Listen for external events from pubsub"""
        async for event in self.pubsub.subscribe("vtuber_events"):
            try:
                await self.handle_pubsub_event(event)
            except Exception as e:
                print(f"Error handling pubsub event: {e}")

    async def handle_pubsub_event(self, event: Dict[str, Any]):
        """Handle different types of pubsub events"""
        event_type = event.get("type")
        session_id = event.get("session_id")
        
        if session_id not in self.active_sessions:
            print(f"No active session for {session_id}")
            return
            
        vtuber = self.active_sessions[session_id]
        
        if event_type == "interrupt":
            vtuber.interrupt(heard_sentence=event.get("heard_sentence", ""))
        elif event_type == "new_prompt":
            # Queue a new conversation without interrupting current one
            await self.queue_conversation(vtuber, event.get("prompt"))
        elif event_type == "change_persona":
            # Handle persona change
            new_persona = event.get("persona")
            await self.update_persona(vtuber, new_persona)
        elif event_type == "tip":
            # Handle tip event with both chat and NFT minting
            amount = event.get("amount")
            currency = event.get("currency", "USD")
            username = event.get("username", "Anonymous")
            wallet_address = event.get("wallet_address")
            
            # Start both processes concurrently
            await asyncio.gather(
                self.handle_tip_chat(vtuber, amount, currency, username),
                self.handle_tip_rewards(amount, wallet_address, username)
            )

    async def handle_tip_chat(self, vtuber: OpenLLMVTuberMain, amount: float, 
                            currency: str, username: str):
        """Handle the chat response to a tip"""
        try:
            # Interrupt current conversation if any
            vtuber.interrupt()
            
            # Format tip message with NFT info
            prompt = (
                f"A viewer named {username} just sent me a tip of {amount} {currency}! "
                "They will receive a special NFT as a thank you. "
                "Please express gratitude and excitement about both the tip and sending them an NFT. "
                "Make it personal and reference the amount and username in your response."
            )
            
            # Queue the response to the tip
            await self.queue_conversation(vtuber, prompt)
            
            # Log the tip
            logger.info(f"Received tip: {amount} {currency} from {username}")
            
        except Exception as e:
            logger.error(f"Error handling tip chat: {e}")

    async def handle_tip_rewards(self, amount: float, wallet_address: Optional[str], 
                               username: str):
        """Handle blockchain rewards for tips"""
        try:
            if not wallet_address:
                logger.warning(f"No wallet address provided for {username}'s tip")
                return

            # Determine NFT tier based on tip amount
            nft_tier = self.determine_nft_tier(amount)
            
            # Queue the NFT minting transaction
            tx_hash = await self.mint_nft(wallet_address, nft_tier)
            
            logger.info(
                f"NFT minting initiated for {username} "
                f"(wallet: {wallet_address[:8]}...), "
                f"tier: {nft_tier}, tx: {tx_hash}"
            )
            
            # Optionally wait for confirmation
            await self.wait_for_transaction(tx_hash)
            
        except Exception as e:
            logger.error(f"Error handling tip rewards: {e}")

    def determine_nft_tier(self, amount: float) -> int:
        """Determine NFT tier based on tip amount"""
        if amount >= 100:
            return 3  # Legendary
        elif amount >= 50:
            return 2  # Rare
        return 1     # Common

    async def mint_nft(self, wallet_address: str, tier: int) -> str:
        """Mint an NFT for the tipper"""
        try:
            if not self.nft_contract:
                raise ValueError("NFT contract not initialized")

            # Prepare the transaction
            tx = await self.nft_contract.functions.mint(
                wallet_address,
                tier,
                int(datetime.now().timestamp())  # Optional timestamp
            ).build_transaction({
                'from': self.open_llm_vtuber_main_config.get("MINTER_ADDRESS"),
                'nonce': self.w3.eth.get_transaction_count(
                    self.open_llm_vtuber_main_config.get("MINTER_ADDRESS")
                ),
            })

            # Sign and send the transaction
            signed_tx = self.w3.eth.account.sign_transaction(
                tx, 
                self.open_llm_vtuber_main_config.get("MINTER_PRIVATE_KEY")
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error minting NFT: {e}")
            raise

    async def wait_for_transaction(self, tx_hash: str, max_attempts: int = 50):
        """Wait for transaction confirmation"""
        for _ in range(max_attempts):
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                if receipt and receipt['status'] == 1:
                    logger.info(f"Transaction {tx_hash} confirmed")
                    return receipt
                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(1)
        raise TimeoutError(f"Transaction {tx_hash} not confirmed after {max_attempts} attempts")

    async def queue_conversation(self, vtuber: OpenLLMVTuberMain, prompt: str):
        """Queue a new conversation to start after current one completes"""
        try:
            # Wait for any current conversation to complete
            while vtuber._continue_exec_flag.is_set():
                await asyncio.sleep(0.1)
            
            # Start new conversation
            response = vtuber.conversation_chain(prompt)
            return response
        except Exception as e:
            print(f"Error queuing conversation: {e}")
    
    async def update_persona(self, vtuber: OpenLLMVTuberMain, new_persona: str):
        """Update the vtuber's persona"""
        try:
            # Interrupt current conversation if any
            vtuber.interrupt()
            
            # Update system prompt with new persona
            new_system_prompt = self.load_persona_prompt(new_persona)
            vtuber.llm.system = new_system_prompt
            
            # Optionally send confirmation message
            await vtuber.conversation_chain("Persona updated! How may I help you?")
        except Exception as e:
            print(f"Error updating persona: {e}")

    async def websocket_endpoint(self, websocket: WebSocket):
        """Existing WebSocket handler"""
        await websocket.accept()
        session_id = str(uuid.uuid4())
        
        try:
            vtuber = OpenLLMVTuberMain(self.open_llm_vtuber_main_config, websocket=websocket)
            self.active_sessions[session_id] = vtuber
            
            # Existing WebSocket handling code...
            
        finally:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

    def _initialize_components(
        self, websocket: WebSocket
    ) -> tuple[Live2dModel, OpenLLMVTuberMain, AudioPayloadPreparer]:
        """
        Initialize or reinitialize all necessary components with current configuration.

        Args:
            websocket: The WebSocket connection to send messages through

        Returns:
            tuple: (Live2dModel instance, OpenLLMVTuberMain instance, AudioPayloadPreparer instance)
        """
        l2d = Live2dModel(self.open_llm_vtuber_main_config["LIVE2D_MODEL"])
        open_llm_vtuber = OpenLLMVTuberMain(self.open_llm_vtuber_main_config)
        audio_preparer = AudioPayloadPreparer()

        # Set up the audio playback function
        def _play_audio_file(sentence: str | None, filepath: str | None) -> None:
            if filepath is None:
                print("No audio to be streamed. Response is empty.")
                return

            if sentence is None:
                sentence = ""
            print(f">> Playing {filepath}...")
            payload, duration = audio_preparer.prepare_audio_payload(
                audio_path=filepath,
                display_text=sentence,
                expression_list=l2d.extract_emotion(sentence),
            )
            print("Payload send.")

            async def _send_audio():
                await websocket.send_text(json.dumps(payload))
                await asyncio.sleep(duration)

            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(_send_audio())
            new_loop.close()

            print("Audio played.")

        open_llm_vtuber.set_audio_output_func(_play_audio_file)
        return l2d, open_llm_vtuber, audio_preparer

    def _setup_routes(self):
        """Sets up the WebSocket and broadcast routes."""

        # the connection between this server and the frontend client
        # The version 2 of the client-ws. Introduces breaking changes.
        # This route will initiate its own main.py instance and conversation loop
        @self.app.websocket("/client-ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            await websocket.send_text(
                json.dumps({"type": "full-text", "text": "Connection established"})
            )

            self.connected_clients.append(websocket)
            print("Connection established")

            # Initialize components
            l2d, open_llm_vtuber, _ = self._initialize_components(websocket)

            await websocket.send_text(
                json.dumps({"type": "set-model", "text": l2d.model_info})
            )
            print("Model set")
            received_data_buffer = np.array([])
            # start mic
            await websocket.send_text(
                json.dumps({"type": "control", "text": "start-mic"})
            )

            conversation_task = None

            try:
                while True:
                    print(".", end="")
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    # print(f"\033\n Received ws req: {data.get('type')}\033[0m\n")

                    if data.get("type") == "interrupt-signal":
                        print("Start receiving audio data from front end.")
                        if conversation_task is not None:
                            print(
                                "\033[91mLLM hadn't finish itself. Interrupting it...",
                                "heard response: \n",
                                data.get("text"),
                                "\033[0m\n",
                            )
                            open_llm_vtuber.interrupt(data.get("text"))
                            # conversation_task.cancel()

                    elif data.get("type") == "mic-audio-data":
                        received_data_buffer = np.append(
                            received_data_buffer,
                            np.array(
                                list(data.get("audio").values()), dtype=np.float32
                            ),
                        )
                        print("*", end="")

                    elif data.get("type") == "mic-audio-end":
                        print("Received audio data end from front end.")
                        await websocket.send_text(
                            json.dumps({"type": "full-text", "text": "Thinking..."})
                        )
                        audio = received_data_buffer
                        received_data_buffer = np.array([])

                        async def _run_conversation():
                            try:
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "control",
                                            "text": "conversation-chain-start",
                                        }
                                    )
                                )
                                await asyncio.to_thread(
                                    open_llm_vtuber.conversation_chain,
                                    user_input=audio,
                                )
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "control",
                                            "text": "conversation-chain-end",
                                        }
                                    )
                                )
                                print("One Conversation Loop Completed")
                            except asyncio.CancelledError:
                                print("Conversation task was cancelled.")
                            except InterruptedError as e:
                                print(f"😢Conversation was interrupted. {e}")

                        conversation_task = asyncio.create_task(_run_conversation())
                    elif data.get("type") == "fetch-configs":
                        config_files = self._scan_config_alts_directory()
                        await websocket.send_text(
                            json.dumps({"type": "config-files", "files": config_files})
                        )
                    elif data.get("type") == "switch-config":
                        config_file = data.get("file")
                        if config_file:
                            new_config = self._load_config_from_file(config_file)
                            if new_config:
                                # Update configuration
                                self.open_llm_vtuber_main_config.update(new_config)

                                # Reinitialize components with new configuration
                                l2d, open_llm_vtuber, _ = self._initialize_components(
                                    websocket
                                )

                                # Send confirmation and model info
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "config-switched",
                                            "message": f"Switched to config: {config_file}",
                                        }
                                    )
                                )
                                await websocket.send_text(
                                    json.dumps(
                                        {"type": "set-model", "text": l2d.model_info}
                                    )
                                )
                                print(f"Configuration switched to {config_file}")
                    elif data.get("type") == "fetch-backgrounds":
                        bg_files = self._scan_bg_directory()
                        await websocket.send_text(
                            json.dumps({"type": "background-files", "files": bg_files})
                        )
                    else:
                        print("Unknown data type received.")

            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
                open_llm_vtuber = None

    def _scan_config_alts_directory(self) -> List[str]:
        config_files = ["conf.yaml"]  # default config file
        config_alts_dir = self.open_llm_vtuber_main_config.get(
            "CONFIG_ALTS_DIR", "config_alts"
        )
        for root, _, files in os.walk(config_alts_dir):
            for file in files:
                if file.endswith(".yaml"):
                    config_files.append(file)
        return config_files

    def _load_config_from_file(self, filename: str) -> Dict:
        """
        Load configuration from a YAML file with robust encoding handling.
        
        Args:
            filename: Name of the config file
            
        Returns:
            Dict: Loaded configuration or None if loading fails
        """
        if filename == "conf.yaml":
            return load_config_with_env("conf.yaml")
        
        config_alts_dir = self.open_llm_vtuber_main_config.get("CONFIG_ALTS_DIR", "config_alts")
        file_path = os.path.join(config_alts_dir, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"Config file not found: {file_path}")
            return None
            
        # Try common encodings first
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'ascii']
        content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                    break
            except UnicodeDecodeError:
                continue
                
        if content is None:
            # Try detecting encoding as last resort
            try:
                with open(file_path, 'rb') as file:
                    raw_data = file.read()
                detected = chardet.detect(raw_data)
                if detected['encoding']:
                    content = raw_data.decode(detected['encoding'])
            except Exception as e:
                logger.error(f"Error detecting encoding for config file {file_path}: {e}")
                return None

        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML from {file_path}: {e}")
            return None

    def _scan_bg_directory(self) -> List[str]:
        bg_files = []
        bg_dir = os.path.join("static", "bg")
        for root, _, files in os.walk(bg_dir):
            for file in files:
                if file.endswith((".jpg", ".jpeg", ".png", ".gif")):
                    bg_files.append(file)
        return bg_files

    def _mount_static_files(self):
        """Mounts static file directories."""
        self.app.mount(
            "/live2d-models",
            StaticFiles(directory="live2d-models"),
            name="live2d-models",
        )
        self.app.mount("/", StaticFiles(directory="./static", html=True), name="static")

    def run(self, host: str = "0.0.0.0", port: int = 8000, log_level: str = "info"):
        """Runs the FastAPI application using Uvicorn."""
        import uvicorn

        uvicorn.run(self.app, host=host, port=port, log_level=log_level)

    @staticmethod
    def clean_cache():
        """Clean the cache directory by removing and recreating it."""
        cache_dir = "./cache"
        if (os.path.exists(cache_dir)):
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir)

    def init_nft_contract(self):
        """Initialize the NFT contract connection"""
        contract_address = self.open_llm_vtuber_main_config.get("NFT_CONTRACT_ADDRESS")
        contract_abi = self.open_llm_vtuber_main_config.get("NFT_CONTRACT_ABI")
        if contract_address and contract_abi:
            return self.w3.eth.contract(address=contract_address, abi=contract_abi)
        return None


def load_config_with_env(path) -> dict:
    """
    Load the configuration file with environment variables.

    Parameters:
    - path (str): The path to the configuration file.

    Returns:
    - dict: The configuration dictionary.

    Raises:
    - FileNotFoundError if the configuration file is not found.
    - yaml.YAMLError if the configuration file is not a valid YAML file.
    """
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()

    # Match ${VAR_NAME}
    pattern = re.compile(r"\$\{(\w+)\}")

    # replace ${VAR_NAME} with os.getenv('VAR_NAME')
    def replacer(match):
        env_var = match.group(1)
        return os.getenv(
            env_var, match.group(0)
        )  # return the original string if the env var is not found

    content = pattern.sub(replacer, content)

    # Load the yaml file
    return yaml.safe_load(content)


if __name__ == "__main__":

    atexit.register(WebSocketServer.clean_cache)

    # Load configurations from yaml file
    config = load_config_with_env("conf.yaml")

    config["LIVE2D"] = True  # make sure the live2d is enabled

    # Initialize and run the WebSocket server
    server = WebSocketServer(open_llm_vtuber_main_config=config)
    server.run(host=config["HOST"], port=config["PORT"])
