from typing import Type
from .llm_interface import LLMInterface
from .ollama import LLM as OllamaLLM
from .memGPT import LLM as MemGPTLLM
from .fake_llm import LLM as FakeLLM
from .claude import LLM as ClaudeLLM
from .hfllama import LLM as HFLlamaLLM
from .hfendpoint import LLM as HFEndpointLLM
import os


class LLMFactory:
    @staticmethod
    def get_config_value(kwargs: dict, key: str, env_key: str = None, default=None):
        """Get configuration value prioritizing environment variables over config values.
        
        Args:
            kwargs (dict): Configuration dictionary
            key (str): Key to look up in kwargs
            env_key (str, optional): Environment variable name. Defaults to key if not provided.
            default: Default value if neither env var nor kwargs exist
            
        Returns:
            The value from environment variable, kwargs, or default
        """
        env_key = env_key or key
        return os.getenv(env_key) or kwargs.get(key, default)

    @staticmethod
    def create_llm(llm_provider, **kwargs) -> Type[LLMInterface]:
        cfg = LLMFactory.get_config_value  # Alias for shorter lines
        
        if llm_provider == "ollama":
            return OllamaLLM(
                system=cfg(kwargs, "SYSTEM_PROMPT"),
                base_url=cfg(kwargs, "BASE_URL"),
                model=cfg(kwargs, "MODEL"),
                llm_api_key=cfg(kwargs, "LLM_API_KEY"),
                project_id=cfg(kwargs, "PROJECT_ID"),
                organization_id=cfg(kwargs, "ORGANIZATION_ID"),
                verbose=cfg(kwargs, "VERBOSE", default=False),
            )
        elif llm_provider == "mem0":
            from llm.mem0_llm import LLM as Mem0LLM
            return Mem0LLM(
                user_id=cfg(kwargs, "USER_ID"),
                system=cfg(kwargs, "SYSTEM_PROMPT"),
                base_url=cfg(kwargs, "BASE_URL"),
                model=cfg(kwargs, "MODEL"),
                llm_api_key=cfg(kwargs, "LLM_API_KEY"),
                project_id=cfg(kwargs, "PROJECT_ID"),
                organization_id=cfg(kwargs, "ORGANIZATION_ID"),
                mem0_config=kwargs.get("MEM0_CONFIG"),  # Special case for nested config
                verbose=cfg(kwargs, "VERBOSE", default=False)
            )
        elif llm_provider == "memgpt":
            return MemGPTLLM(
                base_url=cfg(kwargs, "BASE_URL"),
                server_admin_token=cfg(kwargs, "ADMIN_TOKEN"),
                agent_id=cfg(kwargs, "AGENT_ID"),
                verbose=cfg(kwargs, "VERBOSE", default=False),
            )
        elif llm_provider == "claude":
            return ClaudeLLM(
                system=cfg(kwargs, "SYSTEM_PROMPT"),
                base_url=cfg(kwargs, "BASE_URL"),
                model=cfg(kwargs, "MODEL"),
                llm_api_key=cfg(kwargs, "LLM_API_KEY"),
                verbose=cfg(kwargs, "VERBOSE", default=False),
            )
        elif llm_provider == "hfllama":
            return HFLlamaLLM(
                system=cfg(kwargs, "SYSTEM_PROMPT"),
                base_url=cfg(kwargs, "BASE_URL"),
                model=cfg(kwargs, "MODEL", env_key="HF_MODEL"),
                llm_api_key=cfg(kwargs, "LLM_API_KEY", env_key="HF_TOKEN"),
                verbose=cfg(kwargs, "VERBOSE", default=False),
            )
        elif llm_provider == "hfendpoint":
            return HFEndpointLLM(
                system=cfg(kwargs, "SYSTEM_PROMPT"),
                base_url=cfg(kwargs, "BASE_URL", env_key="HF_ENDPOINT_URL"),
                model=cfg(kwargs, "MODEL", env_key="HF_MODEL"),
                llm_api_key=cfg(kwargs, "LLM_API_KEY", env_key="HF_TOKEN"),
                verbose=cfg(kwargs, "VERBOSE", default=False),
            )
        elif llm_provider == "fakellm":
            return FakeLLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")


# 使用工廠創建 LLM 實例
# llm_instance = LLMFactory.create_llm("ollama", **config_dict)
