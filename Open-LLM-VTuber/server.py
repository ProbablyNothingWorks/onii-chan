import os
import re
import shutil
import atexit
import json
import asyncio
from typing import List, Dict
import yaml
import numpy as np
from fastapi import FastAPI, WebSocket, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
from main import OpenLLMVTuberMain
from live2d_model import Live2dModel
from tts.stream_audio import AudioPayloadPreparer
import chardet
from loguru import logger
import redis.asyncio as aioredis
from decimal import Decimal
from prompts.crypto_reactions import get_token_specific_reactions, format_tip_response
from prompts.intent_classifier import classify_message, MessageIntent
from prompts.ir_reactions import format_ir_response


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
        self.redis_client = None
        self.tip_reaction_task = None
        
        self._setup_routes()
        self._mount_static_files()
        self.app.include_router(self.router)

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

    async def setup_redis(self):
        """Initialize Redis connection and subscription"""
        print("Setting up Redis connection...")
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                self.redis_client = await aioredis.from_url('redis://redis:6379')
                self.pubsub = self.redis_client.pubsub()
                # Subscribe to both channels
                await self.pubsub.subscribe('crypto_tips', 'vtuber_events')
                print("Redis subscriptions established")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Failed to connect to Redis (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"Failed to connect to Redis after {max_retries} attempts, ignoring")

    async def handle_tip(self, tip_data: dict, websocket: WebSocket, open_llm_vtuber: OpenLLMVTuberMain):
        """Process incoming crypto tip and generate VTuber response"""
        print(f"\n=== Processing Tip ===\nData: {tip_data}")
        
        token = tip_data.get('token', 'UNKNOWN')
        amount = Decimal(tip_data.get('amount', 0))
        tipper = tip_data.get('tipper', 'anonymous supporter')
        message = tip_data.get('message', '')
        
        # Get the base reaction from crypto_reactions
        tip_reaction = format_tip_response(token, float(amount))
        # tip_reaction = 'thank you'
        
        # Create a context-aware prompt that maintains character consistency
        user_prompt = f"""
[Event: Received a crypto tip]
Tip Amount: {amount} {token}
From: {tipper}
{f'Their Message: "{message}"' if message else ''}

Base Reaction: {tip_reaction}

Respond to this tip while maintaining your character's personality. Incorporate elements from the base reaction but express them in your own unique way. If they included a message, acknowledge it briefly.
"""

        try:
            if amount > 0:
                await websocket.send_text(
                    json.dumps({"type": "full-text", "text": "💰 Received a crypto tip!"})
                )
                
                response = await asyncio.to_thread(
                    open_llm_vtuber.conversation_chain,
                    user_input=user_prompt
                )
                
                print(f"Successfully responded to {token} tip from {tipper}")
        except Exception as e:
            print(f"Error handling tip: {e}")

    async def monitor_events(self, websocket: WebSocket, open_llm_vtuber: OpenLLMVTuberMain):
        """Monitor Redis for both tips and chat messages"""
        try:
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message and message['type'] == 'message':
                    try:
                        message_data = message['data'].decode('utf-8') if isinstance(message['data'], bytes) else message['data']
                        print(f"DEBUG: Received Redis message: {message_data}")
                        
                        data = json.loads(message_data)
                        event_type = data.get('type')
                        
                        if event_type == 'tip':
                            # Handle crypto tips
                            if all(k in data for k in ['token', 'amount']):
                                await self.handle_tip(data, websocket, open_llm_vtuber)
                            else:
                                print("Invalid tip data format")
                                
                        elif event_type == 'chat':
                            # Handle chat messages
                            if 'text' in data:
                                response = await self.handle_message(
                                    data['text'],
                                    websocket,
                                    open_llm_vtuber
                                )
                                await websocket.send_text(
                                    json.dumps({
                                        "type": "full-text",
                                        "text": response,
                                        "session_id": data.get("session_id", "default")
                                    })
                                )
                            else:
                                print("Invalid chat data format")
                                
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in event monitor: {e}")

    def _setup_routes(self):
        """Sets up the WebSocket and broadcast routes."""

        # Add this new endpoint for text chat
        @self.app.websocket("/text-ws")
        async def text_websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            await self.setup_redis()

            await websocket.send_text(
                json.dumps({"type": "full-text", "text": "Text chat connection established"})
            )

            # Initialize components
            _, open_llm_vtuber, _ = self._initialize_components(websocket)
            
            try:
                while True:
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    if data.get("type") == "text-message":
                        response = await self.handle_message(
                            data.get("text", ""), 
                            websocket, 
                            open_llm_vtuber
                        )
                        
                        # Send the response back to the client
                        await websocket.send_text(
                            json.dumps({
                                "type": "full-text",
                                "text": response
                            })
                        )
            
            except WebSocketDisconnect:
                print("Text chat client disconnected")

        # the existing voice chat endpoint
        @self.app.websocket("/client-ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            await self.setup_redis()
            
            await websocket.send_text(
                json.dumps({"type": "full-text", "text": "Connection established"})
            )

            self.connected_clients.append(websocket)
            print("Connection established")

            # Initialize components
            l2d, open_llm_vtuber, _ = self._initialize_components(websocket)
            
            # Start event monitoring task (replaces tip_reaction_task)
            self.event_monitor_task = asyncio.create_task(
                self.monitor_events(websocket, open_llm_vtuber)
            )
            
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
                if self.tip_reaction_task:
                    self.tip_reaction_task.cancel()
                if self.redis_client:
                    await self.redis_client.close()
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

    async def handle_message(self, message: str, websocket: WebSocket, open_llm_vtuber: OpenLLMVTuberMain):
        """Process incoming messages with intent classification"""
        intent, confidence = await classify_message(message, open_llm_vtuber.llm_client)
        
        if intent == MessageIntent.INVESTOR_RELATIONS and confidence > 0.8:
            # Determine the type of IR query
            ir_types = ["tokenomics", "fundraising", "business_model", "partnerships"]
            
            type_prompt = f"""
            Classify this investor relations question into one of these categories: {', '.join(ir_types)}
            Question: {message}
            Respond with only the category name.
            """
            query_type = await asyncio.to_thread(
                open_llm_vtuber.conversation_chain,
                user_input=type_prompt
            )
            query_type = query_type.strip().lower()
            
            ir_context = format_ir_response(query_type)
            
            response = await asyncio.to_thread(
                open_llm_vtuber.conversation_chain,
                user_input=f"{ir_context}\n\nUser question: {message}"
            )
            return response
            
        elif intent == MessageIntent.CRYPTO_TIP:
            tip_response = await self.handle_tip(message, websocket, open_llm_vtuber)
            return tip_response
            
        else:
            # Handle general chat
            response = await asyncio.to_thread(
                open_llm_vtuber.conversation_chain,
                user_input=message
            )
            return response


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
