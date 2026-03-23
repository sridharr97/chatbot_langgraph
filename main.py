import duckdb
import argparse
import os, getpass
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from src.graph import create_graph

load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

def setup_database():
    """
    Sets up the DuckDB database and populates it with sample data.
    """
    con = duckdb.connect('my_database.db')
    con.execute("CREATE OR REPLACE TABLE employees (id INTEGER, name VARCHAR, department VARCHAR, salary INTEGER)")
    con.execute("INSERT INTO employees VALUES (1, 'Alice', 'Engineering', 100000)")
    con.execute("INSERT INTO employees VALUES (2, 'Bob', 'Engineering', 120000)")
    con.execute("INSERT INTO employees VALUES (3, 'Charlie', 'Marketing', 90000)")
    con.execute("INSERT INTO employees VALUES (4, 'David', 'Sales', 80000)")
    con.execute("INSERT INTO employees VALUES (5, 'Eve', 'Sales', 85000)")
    con.close()

def main():
    """
    Main function to run the chatbot agent.
    """
    # Setup environment
    _set_env("OPENAI_API_KEY")

    # Setup database
    setup_database()

    # Parse arguments
    parser = argparse.ArgumentParser(description="LangGraph Chatbot Agent")
    parser.add_argument("query", type=str, help="The user query")
    args = parser.parse_args()

    # Instantiate LLM globally for the project
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

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
    print(final_state["final_answer"])

if __name__ == "__main__":
    main()