from huggingface_hub import InferenceClient
from typing import Iterator, Optional
from .llm_interface import LLMInterface

class LLM(LLMInterface):
    def __init__(
        self,
        model_id: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        hf_token: str = None,
        max_new_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        system_prompt: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize LLM client through HuggingFace (optimized for Llama).

        Args:
            model_id (str): HF Model ID for Llama model
            hf_token (str): HuggingFace API token
            max_new_tokens (int): Maximum number of tokens to generate
            temperature (float): Sampling temperature
            top_p (float): Nucleus sampling parameter
            system_prompt (Optional[str]): System prompt for the conversation
            verbose (bool): Whether to print debug info
        """
        if not hf_token:
            raise ValueError("HuggingFace token is required")

        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.verbose = verbose
        self.system_prompt = system_prompt

        # Initialize HF client
        self.client = InferenceClient(
            model=model_id,
            token=hf_token
        )

        # Initialize conversation with system prompt if provided
        self.messages = []
        if system_prompt:
            self.messages.append({
                "role": "system",
                "content": system_prompt
            })

    def _format_llama_chat(self) -> str:
        """
        Format messages for Llama chat format.

        Returns:
            str: Formatted prompt following Llama chat template
        """
        formatted = ""

        # Add system prompt if it exists and isn't in messages
        if self.system_prompt and not any(msg["role"] == "system" for msg in self.messages):
            formatted += f"<s>[INST] <<SYS>>\n{self.system_prompt}\n<</SYS>>\n\n"

        # Add conversation history
        for i, msg in enumerate(self.messages):
            if msg["role"] == "system":
                continue  # Already handled above
            elif msg["role"] == "user":
                if i == 0 or self.messages[i-1]["role"] == "assistant":
                    formatted += f"<s>[INST] {msg['content']} [/INST]"
                else:
                    formatted += f"{msg['content']} [/INST]"
            elif msg["role"] == "assistant":
                formatted += f"{msg['content']}</s>"

        return formatted

    def chat_iter(self, prompt: str) -> Iterator[str]:
        """
        Send message to model and yield response tokens.

        Args:
            prompt (str): User message

        Yields:
            str: Response tokens
        """
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # Add user message to history
        self.messages.append({"role": "user", "content": prompt})

        try:
            response_text = ""
            formatted_prompt = self._format_llama_chat()

            # Stream response from model
            for token in self.client.text_generation(
                formatted_prompt,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                stream=True,
                stop_sequences=["</s>", "[INST]"]  # Stop at end of generation or new instruction
            ):
                response_text += token
                yield token

            # Clean up response and add to history
            response_text = response_text.strip()
            self.messages.append({
                "role": "assistant",
                "content": response_text
            })

        except Exception as e:
            if self.verbose:
                print(f"Error in chat: {str(e)}")
            raise

    def handle_interrupt(self, heard_response: str) -> None:
        """
        Handle interruption by updating the last assistant message.

        Args:
            heard_response (str): The heard portion of the response
        """
        if self.messages and self.messages[-1]["role"] == "assistant":
            # Update last assistant message with only heard portion
            self.messages[-1]["content"] = heard_response

    def clear_history(self) -> None:
        """Clear conversation history except system prompt."""
        if self.system_prompt:
            self.messages = [{
                "role": "system",
                "content": self.system_prompt
            }]
        else:
            self.messages = []
