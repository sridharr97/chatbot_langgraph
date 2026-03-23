# LangGraph Chatbot Agent

This project implements a LangGraph-based chatbot agent in Python that can answer user queries by generating and executing SQL queries on a DuckDB database.

## Tech Stack
- Python
- LangGraph
- LangChain (for LLM integration)
- DuckDB (for database execution)
- Pydantic (for state modeling)
- OpenAI (for LLM calls)

## Project Structure

```
/chatbot_using_langgraph/
├───.env                  # For API keys (not used directly, but can store other env vars)
├───.gitignore
├───main.py               # CLI entry point
├───pyproject.toml        # Project dependencies
├───README.md             # This file
├───src/
│   ├───__init__.py
│   ├───graph.py          # LangGraph definition
│   ├───state.py          # Pydantic state model
│   ├───nodes/
│   │   ├───__init__.py
│   │   ├───answer.py     # Generates natural language answer
│   │   ├───check.py      # Checks SQL execution result
│   │   ├───execute.py    # Executes SQL (Tool node)
│   │   ├───fix.py        # Fixes SQL queries
│   │   ├───generate.py   # Generates SQL
│   │   ├───plan.py       # Plans SQL query
│   │   ├───understand.py # Understands user query
│   │   └───validate.py   # Validates SQL
│   └───tools/
│       ├───__init__.py
│       └───duckdb_tool.py  # DuckDB execution tool
└───uv.lock               # uv lock file
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd chatbot_using_langgraph
    ```

2.  **Install dependencies:**
    This project uses `uv` for dependency management.
    ```bash
    uv pip install .
    ```

3.  **Set OpenAI API Key:**
    The project uses OpenAI for LLM calls. Ensure your `OPENAI_API_KEY` is set in your system environment variables. When you run the application, if the key is not found, you will be prompted to enter it.

## How to Run

To run the chatbot agent, execute the `main.py` script with your query as an argument:

```bash
python3 main.py "How many employees are in the engineering department?"
```

**Example Query:**
`python3 main.py "What is the average salary in the sales department?"`

## Mock Database

The `main.py` script automatically sets up a DuckDB database named `my_database.db` with a sample `employees` table. The schema for this table is:

```
Table: employees
Columns:
- id (INTEGER)
- name (VARCHAR)
- department (VARCHAR)
- salary (INTEGER)
```
