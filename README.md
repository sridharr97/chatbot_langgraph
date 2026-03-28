# Multi-Agent SQL Chatbot (LangGraph)

This project implements a modular, multi-agent chatbot system using LangGraph. It features an **Orchestrator Agent** that manages complex user queries by breaking them down and delegating database-related tasks to a specialized **SQL QA Sub-Agent**.

## Architecture

The system follows a hierarchical agent pattern:
1.  **Orchestrator Agent**: The high-level controller that receives user queries, plans the execution, and calls tools.
2.  **SQL QA Sub-Agent**: A specialized agent tool that handles natural language to SQL generation, validation, execution on DuckDB, and answer synthesis.

This architecture is designed for scalability, allowing additional specialized sub-agents (e.g., for document retrieval) to be easily integrated as tools in the future.

## Tech Stack
- **Framework**: Python, LangGraph, LangChain
- **Database**: DuckDB
- **API**: FastAPI
- **Frontend**: Vue.js (Vite)
- **LLM**: OpenAI (GPT-4o)

## Project Structure

```
/chatbot_using_langgraph/
├───main.py               # CLI entry point for direct SQL Agent testing
├───ingest_database.py    # Script to setup mock DuckDB data
├───orchestrator/         # High-level Orchestrator Agent
│   ├───graph.py          # Orchestrator graph definition
│   └───state.py          # Orchestrator state model
├───backend/              # FastAPI Server (wraps Orchestrator)
│   └───main.py
├───frontend/             # Vue.js Web Interface
├───src/
│   ├───agents/
│   │   └───sql_agent/    # Specialized SQL QA Sub-Agent
│   │       ├───graph.py  # SQL Agent workflow
│   │       ├───state.py  # SQL Agent state
│   │       └───nodes/    # SQL Agent operational nodes (generate, validate, etc.)
│   ├───tools/            # Shared tools (sql_tool.py wraps SQL Agent)
│   └───logging_config.py # Centralized logging
└───tests/                # Test suite
```

## Setup

1.  **Install dependencies:**
    This project uses `uv` for dependency management.
    ```bash
    uv pip install .
    ```

2.  **Environment Variables:**
    Create a `.env` file in the root or set them in your environment:
    - `OPENAI_API_KEY`: Your OpenAI API key.
    - `ENV`: `local` (default) or `azure`.

3.  **Prepare Database:**
    ```bash
    python3 ingest_database.py
    ```

## How to Run

### 1. Web Application (Orchestrator)
The preferred way to interact with the full multi-agent system.

**Start the Backend:**
```bash
python3 backend/main.py
```
The API will be available at `http://localhost:8000`.

**Start the Frontend:**
```bash
cd frontend
npm install
npm run dev
```
The UI will be available at `http://localhost:5173`.

### 2. CLI (SQL Agent Only)
To test the SQL Sub-Agent directly without the orchestrator:
```bash
python3 main.py "What is the average salary in the sales department?"
```

## SQL Agent Workflow
The SQL sub-agent follows a robust pipeline:
1.  **Understand**: Extracts structured intent.
2.  **Plan**: Generates a query plan based on schema.
3.  **Generate**: Writes DuckDB-compatible SQL.
4.  **Validate**: Checks SQL syntax and safety.
5.  **Execute**: Runs the query on DuckDB.
6.  **Fix (Loop)**: If execution fails, the agent attempts to fix the SQL and retries.
7.  **Answer**: Synthesizes a natural language response from data.
