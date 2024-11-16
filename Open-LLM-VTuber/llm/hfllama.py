from huggingface_hub import InferenceClient
from typing import Iterator
from .llm_interface import LLMInterface

class LLM(LLMInterface):
    def __init__(
        self,
        system: str = None,
        base_url: str = None,
        model: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        llm_api_key: str = None,
        verbose: bool = False,
    ):
        """
        Initialize HuggingFace LLM client.
        """
        self.system = system
        self.model = model
        self.verbose = verbose
        
        # Initialize HF client
        self.client = InferenceClient(
            model=model,
            token=llm_api_key
        )
        
        # Store conversation history
        self.messages = []

    def chat_iter(self, prompt: str) -> Iterator[str]:
        """Send message to model and yield response tokens."""
        self.messages.append({"role": "user", "content": prompt})
        
        try:
            formatted_prompt = self._format_chat()
            response_text = ""
            
            for token in self.client.text_generation(
                formatted_prompt,
                max_new_tokens=128,
                temperature=0.7,
                stream=True,
                stop=["</s>", "[INST]"],
                return_full_text=False
            ):
                response_text += token
                yield token
                
            self.messages.append({
                "role": "assistant", 
                "content": response_text.strip()
            })
                
        except Exception as e:
            if self.verbose:
                print(f"Error in chat: {str(e)}")
            raise

    def _format_chat(self) -> str:
        """Format messages for chat."""
        formatted = ""
        if self.system:
            formatted = f"<s>[INST] <<SYS>>\n{self.system}\n<</SYS>>\n\n"
            
        for i, msg in enumerate(self.messages):
            if msg["role"] == "user":
                if i == 0:
                    formatted += f"<s>[INST] {msg['content']} [/INST]"
                else:
                    formatted += f"{msg['content']} [/INST]"
            elif msg["role"] == "assistant":
                formatted += f"{msg['content']}</s>"
        return formatted

    def handle_interrupt(self, heard_response: str) -> None:
        """Handle interruption by updating the last assistant message."""
        if self.messages and self.messages[-1]["role"] == "assistant":
            self.messages[-1]["content"] = heard_response
