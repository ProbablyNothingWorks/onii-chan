from openai import OpenAI
from typing import Iterator
from .llm_interface import LLMInterface

class LLM(LLMInterface):
    def __init__(
        self,
        model: str = None,
        llm_api_key: str = None,
        system: str = None,
        verbose: bool = False,
        base_url: str = None,
        project_id: str = None,  
        organization_id: str = None,  
        **kwargs  
    ):
        if not base_url:
            raise ValueError("base_url is required for HuggingFace Endpoints")
            
        self.verbose = verbose
        self.system = system
        print(f"DEBUG: Init with URL {base_url}")
        
        # Ensure base_url ends with /v1/
        if not base_url.endswith('/v1/'):
            base_url = f"{base_url}/v1/"
            
        self.client = OpenAI(
            base_url=base_url,
            api_key=llm_api_key
        )
        
        self.messages = []
        if system:
            self.messages.append({"role": "system", "content": system})

    def chat_iter(self, prompt: str) -> Iterator[str]:
        print(f"DEBUG: Starting chat_iter with prompt: {prompt}")
        
        try:
            # Add the new user message
            messages = list(self.messages)  # Copy existing messages
            messages.append({"role": "user", "content": prompt})
            
            print("DEBUG: Starting chat completion...")
            chat_completion = self.client.chat.completions.create(
                model="tgi",  # Required model name for TGI endpoints
                messages=messages,
                temperature=0.5,
                max_tokens=100,
                stream=True
            )
            
            response_text = ""
            for message in chat_completion:
                if hasattr(message.choices[0].delta, 'content'):
                    token = message.choices[0].delta.content
                    if token is not None:
                        print(f"DEBUG: Got token: {token}")
                        yield token
                        response_text += token
            
            if response_text:
                print("DEBUG: Final response:", response_text)
                self.messages.append({
                    "role": "assistant",
                    "content": response_text
                })
            else:
                fallback = "I apologize, I couldn't generate a response."
                print("DEBUG: Using fallback:", fallback)
                yield fallback
                self.messages.append({
                    "role": "assistant",
                    "content": fallback
                })
                
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            error_response = "I apologize, but I encountered an error."
            yield error_response
            self.messages.append({
                "role": "assistant",
                "content": error_response
            })

    def handle_interrupt(self, heard_response: str) -> None:
        if self.messages and self.messages[-1]["role"] == "assistant":
            self.messages[-1]["content"] = heard_response