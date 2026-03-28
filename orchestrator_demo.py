import os
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

from orchestrator.graph import create_orchestrator_graph
from src.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

def run_demo():
    """
    Demonstrates the orchestrator agent in action.
    """
    # 1. Initialize the LLM
    # Ensure OPENAI_API_KEY is set in your .env file
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # 2. Create the Orchestrator Graph
    app = create_orchestrator_graph(llm)

    # 3. Define the query
    query = "Show total sales by region"
    logger.info(f"\nUser Query: {query}")

    # 4. Invoke the Graph
    # We initialize the state with the user message
    result = app.invoke({
        "messages": [HumanMessage(content=query)],
        "sql_tool_results": []
    })

    # 5. Handle the Final Output (Requirement 5)
    final_message = result["messages"][-1]
    
    print("\n" + "="*50)
    print("ORCHESTRATOR FINAL RESPONSE:")
    print("="*50)
    print(final_message.content)
    print("="*50)

    # 6. Inspect Preserved Metadata (Requirement 4)
    if result.get("sql_tool_results"):
        print("\nPRESERVED METADATA (Full Tool Output):")
        last_result = result["sql_tool_results"][-1]
        print(f"Executed SQL: {last_result.get('sql')}")
        print(f"Status: {last_result.get('status')}")
        print(f"Number of rows in result: {len(last_result.get('data', []))}")
        if last_result.get('data'):
            print(f"Sample data row: {last_result['data'][0]}")

if __name__ == "__main__":
    run_demo()
