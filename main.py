import argparse
import logging
import os
from dotenv import load_dotenv

# LangChain and LangGraph imports
from langchain_core.messages import HumanMessage

# Project imports
from orchestrator.graph import create_orchestrator_graph
from src.llm_config import get_llm
from src.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    """
    Main function to run the multi-agent orchestrator from the CLI.
    """
    # Parse arguments
    parser = argparse.ArgumentParser(description="Multi-Agent Orchestrator CLI")
    parser.add_argument("query", type=str, help="The user query")
    args = parser.parse_args()

    # Get LLM based on environment configuration
    try:
        llm = get_llm()
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        return

    # Create the orchestrator graph with the shared LLM
    # The orchestrator uses a MemorySaver, so we'll need to provide a thread_id in the config.
    app = create_orchestrator_graph(llm)

    # Initial state for the orchestrator
    initial_state = {
        "messages": [HumanMessage(content=args.query)],
        "sql_tool_results": [],
        "orchestrator_retry_count": 0
    }

    # Config with thread_id for persistence
    config = {"configurable": {"thread_id": "cli_user_session"}}

    print(f"\n--- Processing Query: '{args.query}' ---\n")

    try:
        # Invoke the orchestrator graph
        final_state = app.invoke(initial_state, config=config)

        # The final answer is the content of the last message in the state
        messages = final_state.get("messages", [])
        if messages:
            final_answer = messages[-1].content
            print("\nFinal Answer:")
            print("-" * 20)
            print(final_answer)
            print("-" * 20)
        else:
            print("\nNo answer generated.")

    except Exception as e:
        logger.error(f"Error during orchestrator execution: {e}")
        print(f"\nSorry, an error occurred while processing your request: {e}")

if __name__ == "__main__":
    main()
