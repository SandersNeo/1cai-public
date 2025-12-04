from langchain_openai import ChatOpenAI
import os

class LLMFactory:
    """
    Creates LLM instances based on configuration.
    Supports OpenAI and vLLM (via OpenAI-compatible API).
    """
    @staticmethod
    def create(model_name: str = "gpt-4-turbo", temperature: float = 0.0):
        """
        Returns a configured ChatOpenAI instance.
        """
        # Check for vLLM specific configuration
        vllm_api_base = os.getenv("VLLM_API_BASE")
        openai_api_key = os.getenv("OPENAI_API_KEY", "sk-placeholder") # Placeholder for vLLM if no auth needed

        if vllm_api_base:
            # vLLM Configuration
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                openai_api_key=openai_api_key,
                openai_api_base=vllm_api_base,
                max_tokens=4096
            )
        else:
            # Standard OpenAI Configuration
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                openai_api_key=openai_api_key
            )
