import os
from dotenv import load_dotenv

def get_llm():
    """
    Helper to initialize the LLM based on environment variables.
    """
    load_dotenv()
    env = os.getenv("ENV", "local")
    
    if env == "local":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
             raise ValueError("OPENAI_API_KEY is not set in environment. Please set it or check your .env file.")
        return ChatOpenAI(model="gpt-4o", temperature=0)
    
    elif env == "azure":
        try:
            # We assume azure_llm.py is in the search path
            from azure_llm import AzureOpenAIModel
            return AzureOpenAIModel()
        except ImportError:
            raise ImportError("azure_llm.py not found. Ensure it is in the PYTHONPATH if ENV=azure.")
    
    else:
        raise ValueError(f"Unsupported ENV: {env}")
