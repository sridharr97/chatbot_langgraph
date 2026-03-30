# Multi-Agent Orchestrator (LangGraph)

This project implements a modular, multi-agent chatbot system using LangGraph. It features an **Orchestrator Agent** that manages complex user queries by breaking them down and delegating tasks to specialized sub-agents via tools.

## Architecture

The system follows a hierarchical agent pattern:
1.  **Orchestrator Agent**: The high-level controller that receives user queries, plans the execution, and invokes appropriate tools.
2.  **SQL QA Sub-Agent**: A specialized agent that handles natural language to SQL generation, validation, execution on DuckDB, and data analysis.
3.  **Doc QA Sub-Agent**: A specialized agent that answers questions based on content from internal documents (.docx).

This architecture is designed for scalability, allowing additional specialized sub-agents to be easily integrated as tools.

## Tech Stack
- **Framework**: Python, LangGraph, LangChain
- **Database**: DuckDB
- **API**: FastAPI
- **Frontend**: Vue.js (Vite)
- **LLM**: OpenAI (GPT-4o)

## Project Structure

```
/chatbot_using_langgraph/
├───main.py               # CLI entry point to run the Orchestrator
├───ingest_database.py    # Script to setup mock data
├───orchestrator/         # High-level Orchestrator Agent
│   ├───graph.py          # Orchestrator graph definition
│   └───state.py          # Orchestrator state model
├───backend/              # FastAPI Server (wraps Orchestrator)
│   └───main.py
├───frontend/             # Vue.js Web Interface
├───src/
│   ├───llm_config.py     # Centralized LLM initialization
│   ├───agents/
│   │   ├───sql_agent/    # Specialized SQL QA Sub-Agent
│   │   └───doc_agent/    # Specialized Doc QA Sub-Agent
│   ├───tools/            # Tool wrappers (sql_tool.py, doc_tool.py)
│   ├───resources/        # Data resources (schema.json, docs_schema.json, DB/Docs)
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

### 1. Web Application (Full System)
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

### 2. CLI
To interact with the Orchestrator via terminal:
```bash
python3 main.py "Your question here"
```

## System Workflow
1.  **Orchestration**: The Orchestrator receives the query and decides whether to use the SQL tool, the Doc tool, or provide a direct response.
2.  **SQL Execution**: If delegating to the SQL tool, the sub-agent follows a pipeline of Understanding -> Planning -> Generating -> Validating -> Executing -> Answering.
3.  **Doc Retrieval**: If delegating to the Doc tool, the sub-agent selects the relevant document from the schema and generates an answer strictly from its content.
