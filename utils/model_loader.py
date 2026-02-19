import os
import sys
from dotenv import load_dotenv
from utils.config_loader import load_config
from .config_loader import load_config
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
from langchain_openai import AzureChatOpenAI

from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
log=CustomLogger().get_logger(__name__)


class ModelLoader:
    """A class to load and manage different language models and embeddings based on configuration."""

    def __init__(self):
        load_dotenv()
        self._validate_env()
        self.config = load_config()
        log.info("Configuration loaded successfully.", confing_keys=list(self.config.keys()))

    def _validate_env(self):
        """Validate required environment variables.
        Ensures that all necessary environment variables are set.
        """
        required_vars = ["GOOGLE_API_KEY", "GROQ_API_KEY", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT_NAME"]

        self.api_keys = {key:os.getenv(key) for key in required_vars}

        missing_vars = [key for key, value in self.api_keys.items() if not value]

        if missing_vars:
            log.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            raise DocumentPortalException("Missing required environment variables", sys)
        
        log.info("All Environment variables are set properly.", available_keys=[key for key in self.api_keys])

 

    def load_embeddings(self):
        """Load embeddings model based on configuration."""
        try:
            log.info("Loading embeddings model...")
            self.embedding_block = self.config["embedding_model"]

            print("self.embedding_block", self.embedding_block)
            embedding_provider_key = os.getenv("EMBEDDING_PROVIDER", "transformer")

            if embedding_provider_key not in self.embedding_block:
                log.error(f"Embedding Provider not found in embedding_model configuration", provider_key=embedding_provider_key)
                raise DocumentPortalException(f"Embedding Provider 'not found in embedding_model configuration", sys)
            
            embedding_config = self.embedding_block[embedding_provider_key]
            provider = embedding_config.get("provider")
            model_name = embedding_config.get("model_name")

            log.info(f"Selected Embedding : ", provider=provider, model_name=model_name)

            if provider == "google":
                embeddings = GoogleGenerativeAIEmbeddings(
                    model_name=model_name,
                    )
                return embeddings
            
            elif provider == "huggingface":
                embeddings = HuggingFaceEmbeddings(
                    model_name=model_name,
                    )
                return embeddings
            
            elif provider == "azure_openai":
                embeddings = AzureOpenAIEmbeddings(
                    model=model_name,
                    api_key=self.api_keys["AZURE_OPENAI_API_KEY"],
                    endpoint=self.api_keys["AZURE_OPENAI_ENDPOINT"],
                    deployment_name=self.api_keys["AZURE_OPENAI_DEPLOYMENT_NAME"]
                )
                return embeddings
            else:
                log.error(f"Unsupported embedding provider: ", provider=provider)
                raise DocumentPortalException(f"Unsupported embedding provider: {provider}", sys)
                

        except Exception as e:
            log.error(f"Error loading embeddings:", error=str(e))
            raise DocumentPortalException("failed to load embeddings model", sys)

    def load_llm(self):
        """ Load language model based on configuration."""

        try:
            llm_block = self.config["llm"]

            log.info("Loading LLM model...")

            provider_key = os.getenv("LLM_PROVIDER", "groq")

            if provider_key not in llm_block:
                log.error(f"LLM Provider not found in llm configuration", provider_key=provider_key)
                raise DocumentPortalException(f"LLM Provider 'not found in llm configuration", sys)
            
            llm_config = llm_block[provider_key]
            provider = llm_config.get("provider")
            model_name = llm_config.get("model_name")
            temperature = llm_config.get("temperature", 0.2)
            max_tokens = llm_config.get("max_tokens", 2048)

            log.info(f"Selected LLM : ", provider=provider, model_name=model_name, temperature=temperature, max_tokens=max_tokens)

            if provider == "groq":
                llm = ChatGroq(
                    model=model_name,
                    api_key=self.api_keys["GROQ_API_KEY"],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return llm
            elif provider == "google":
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
                return llm
            elif provider == "azure_openai":
                llm = AzureChatOpenAI(
                    model=model_name,
                    api_key=self.api_keys["AZURE_OPENAI_API_KEY"],
                    endpoint=self.api_keys["AZURE_OPENAI_ENDPOINT"],
                    deployment_name=self.api_keys["AZURE_OPENAI_DEPLOYMENT_NAME"],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return llm
            
            else:
                log.error(f"Unsupported LLM provider: ", provider=provider)
                raise DocumentPortalException(f"Unsupported LLM provider: {provider}", sys)
            
        except Exception as e:
            log.error(f"Error loading LLM:", error=str(e))
            raise DocumentPortalException("failed to load LLM model", sys)
        

if __name__ == "__main__":
    model_loader = ModelLoader()
    embeddings = model_loader.load_embeddings()
    print("Embeddings loaded successfully.", embeddings)
    print("---------------------------------------------------")
    print(len(embeddings.embed_query("hello world")))
    llm = model_loader.load_llm()
    print("LLM loaded successfully.", llm)
    print("---------------------------------------------------")
    print(llm.invoke("Hello, how are you?"))
