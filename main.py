import argparse
import logging
from src.agents.sql_agent.graph import create_graph

import os, getpass
from dotenv import load_dotenv
load_dotenv()
ENV = os.getenv("ENV", "azure")

# Configure logging to show process updates in CLI
logging.basicConfig(level=logging.INFO, format='%(message)s')

def get_llm(ENV: str):
    if ENV == "local":
        # import
        from langchain_openai import ChatOpenAI
        
        # Setup environment
        def _set_env(var: str):
            if not os.environ.get(var):
                os.environ[var] = getpass.getpass(f"{var}: ")
        _set_env("OPENAI_API_KEY")

        # Instantiate LLM globally for the project
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        return llm
    
    elif ENV == "azure":
        # import
        from azure_llm import AzureOpenAIModel

        # Instantiate LLM globally for the project
        llm = AzureOpenAIModel()
        return llm
    
    else:
        raise ValueError(f"Unsupported ENV: {ENV}")

def main():
    """
    Main function to run the chatbot agent.
    """
    # Get LLM based on environment
    llm = get_llm(ENV)

    # Parse arguments
    parser = argparse.ArgumentParser(description="LangGraph Chatbot Agent")
    parser.add_argument("query", type=str, help="The user query")
    args = parser.parse_args()



    # Create graph with the shared LLM
    app = create_graph(llm)

    # Invoke graph
    final_state = app.invoke(
        {
            "user_query": args.query,
            "retry_count": 0,
        }
    )

    # Print final answer
    print("\n", final_state["final_answer"])

if __name__ == "__main__":
    main()