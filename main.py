import duckdb
import argparse
from src.graph import create_graph

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
    # Setup database
    setup_database()

    # Parse arguments
    parser = argparse.ArgumentParser(description="LangGraph Chatbot Agent")
    parser.add_argument("query", type=str, help="The user query")
    args = parser.parse_args()

    # Create graph
    app = create_graph()

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