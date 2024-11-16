from huggingface_hub import InferenceClient
from typing import Iterator
from .llm_interface import LLMInterface

class LLM(LLMInterface):
    def __init__(
        self,
        model: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        llm_api_key: str = None,
        system: str = None,
        verbose: bool = False,
        base_url: str = None,  
        project_id: str = None,  
        organization_id: str = None,  
        **kwargs  
    ):
        self.model = model
        self.verbose = verbose
        self.system = system
        
        # Initialize HF client
        self.client = InferenceClient(
            model=model,
            token=llm_api_key
        )
        
        # Initialize messages with system prompt if provided
        self.messages = []
        if system:
            self.messages.append({"role": "system", "content": system})

    def chat_iter(self, prompt: str) -> Iterator[str]:
        """
        Send message to model and yield response tokens.
        Falls back to non-streaming if streaming is not supported.
        """
        self.messages.append({"role": "user", "content": prompt})
        
        try:
            try:
                # First try streaming
                for chunk in self.client.chat_completion(
                    self.messages,
                    stream=True,
                    max_tokens=128,
                    temperature=0.7
                ):
                    token = chunk.choices[0].delta.content
                    if token:
                        yield token
                        
            except Exception as stream_error:
                if self.verbose:
                    print(f"Streaming not supported, falling back to non-streaming: {str(stream_error)}")
                    
                # Fallback to non-streaming
                response = self.client.chat_completion(
                    self.messages,
                    stream=False,
                    max_tokens=128,
                    temperature=0.7
                )
                content = response.choices[0].message.content
                # Yield the entire response as one token
                yield content
                
            # Get the final response text (either from streaming or non-streaming)
            if self.messages[-1]["role"] == "user":  # Make sure we haven't added the response yet
                response_text = content if 'content' in locals() else None
                if not response_text:
                    # Try to reconstruct from streaming if needed
                    response_text = "".join(token for token in response.choices[0].message.content)
                    
                self.messages.append({
                    "role": "assistant",
                    "content": response_text
                })
                
        except Exception as e:
            if self.verbose:
                print(f"Error in chat: {str(e)}")
            raise

    def handle_interrupt(self, heard_response: str) -> None:
        if self.messages and self.messages[-1]["role"] == "assistant":
            self.messages[-1]["content"] = heard_response
