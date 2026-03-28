import os
import getpass
import logging
import asyncio
import json
import csv
import contextvars
from datetime import datetime, date
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# LangChain messages
from langchain_core.messages import HumanMessage

# Import orchestrator graph and logging config
from orchestrator.graph import create_orchestrator_graph
from src.logging_config import setup_logging, reset_log_file

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

ENV = os.getenv("ENV", "local")

# Define temp dir and file
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
LATEST_RESULT_FILE = os.path.join(TEMP_DIR, "latest_query_result.csv")

# Global loop reference
_loop = None

def custom_json_serializer(obj):
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return str(obj)

# --- 1. Status Tracking Handler ---

class UIStatusHandler(logging.Handler):
    """
    Captures specific log patterns to send as UI status updates.
    """
    def __init__(self, queue, loop):
        super().__init__()
        self.queue = queue
        self.loop = loop

    def emit(self, record):
        msg = record.getMessage()
        if "---" in msg:
            # Clean up the message for the UI
            clean_msg = msg.replace("---", "").strip()
            # If it's a node log, format it nicely
            if "NODE:" in clean_msg:
                clean_msg = clean_msg.replace("NODE:", "Processing:").strip()
            if "ORCHESTRATOR: Calling" in clean_msg:
                clean_msg = "Calling SQL QA Tool..."
            
            try:
                self.loop.call_soon_threadsafe(self.queue.put_nowait, clean_msg)
            except:
                pass

# --- 2. Graph and App Init ---

def get_llm(ENV: str):
    if ENV == "local":
        from langchain_openai import ChatOpenAI
        if not os.environ.get("OPENAI_API_KEY"):
             raise ValueError("OPENAI_API_KEY is not set in environment")
        return ChatOpenAI(model="gpt-4o", temperature=0)
    elif ENV == "azure":
        try:
            from azure_llm import AzureOpenAIModel
            return AzureOpenAIModel()
        except ImportError:
            raise ImportError("azure_llm.py not found.")
    else:
        raise ValueError(f"Unsupported ENV: {ENV}")

llm = get_llm(ENV)
graph_app = create_orchestrator_graph(llm)

app = FastAPI(title="LangGraph Orchestrator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    global _loop
    _loop = asyncio.get_running_loop()

class ChatRequest(BaseModel):
    message: str

def save_result_to_csv(data: list):
    """Saves the query result to a CSV file."""
    if not data:
        with open(LATEST_RESULT_FILE, "w", newline="") as f:
            pass
        return
    keys = data[0].keys()
    with open(LATEST_RESULT_FILE, "w", newline="") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)

async def process_graph_stream(request: ChatRequest):
    """
    Generator that yields real-time status updates and final results.
    """
    # Reset log file for every new user query
    reset_log_file()
    
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    status_handler = UIStatusHandler(queue, loop)
    
    # Attach handler to relevant loggers
    src_logger = logging.getLogger("src")
    orch_logger = logging.getLogger("orchestrator")
    src_logger.addHandler(status_handler)
    orch_logger.addHandler(status_handler)

    try:
        # Initial state
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "sql_tool_results": [],
            "orchestrator_retry_count": 0
        }

        # Run graph in a separate task
        # We provide a fixed thread_id to enable persistent memory for this session
        config = {"configurable": {"thread_id": "default_user_session"}}
        graph_task = asyncio.create_task(graph_app.ainvoke(inputs, config=config))

        # Stream status updates from the queue while the graph runs
        while not graph_task.done():
            try:
                # Wait for a status message or graph completion
                done, pending = await asyncio.wait(
                    [asyncio.create_task(queue.get()), graph_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Check if we have a new status message
                for task in done:
                    if task != graph_task:
                        status_msg = task.result()
                        yield json.dumps({"type": "status", "content": status_msg}) + "\n"
                    
            except asyncio.TimeoutError:
                continue

        # Get the final state
        final_state = await graph_task

        # --- Output Mapping ---
        sql_tool_results = final_state.get("sql_tool_results", [])
        last_sql_result = sql_tool_results[-1] if sql_tool_results else None

        if last_sql_result:
            query_result = last_sql_result.get("data")
            if query_result and isinstance(query_result, list):
                 save_result_to_csv(query_result)
                 yield json.dumps({"type": "data", "content": query_result[:100]}, default=custom_json_serializer) + "\n"
            
            generated_sql = last_sql_result.get("sql")
            if generated_sql:
                yield json.dumps({"type": "query", "content": generated_sql}, default=custom_json_serializer) + "\n"

        messages = final_state.get("messages", [])
        final_answer = messages[-1].content if messages else "No answer generated."
        yield json.dumps({"type": "result", "content": final_answer}, default=custom_json_serializer) + "\n"

    except asyncio.CancelledError:
        logger.info("Request cancelled.")
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"
    finally:
        src_logger.removeHandler(status_handler)
        orch_logger.removeHandler(status_handler)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(process_graph_stream(request), media_type="application/x-ndjson")

@app.get("/download")
async def download_endpoint():
    if os.path.exists(LATEST_RESULT_FILE):
        return FileResponse(LATEST_RESULT_FILE, media_type='text/csv', filename="query_result.csv")
    raise HTTPException(status_code=404, detail="No result file found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
