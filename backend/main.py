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

# Import graph and logging config
from src.graph import create_graph
from src.logging_config import setup_logging

# Initialize logging as per requirement
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
    # Handle pandas/duckdb Timestamps if they have an isoformat or __str__
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return str(obj)

# Initialize LLM and LangGraph
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
graph_app = create_graph(llm)

# Initialize FastAPI app
app = FastAPI(title="LangGraph Chatbot API")

# Add CORS middleware
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
        # Create empty file
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
    Generator that yields the final result and the data preview.
    Runtime logs are no longer streamed.
    """
    try:
        # Run graph.invoke in a thread
        def run_with_context():
            return graph_app.invoke({"user_query": request.message, "retry_count": 0})

        future = asyncio.get_running_loop().run_in_executor(None, run_with_context)
        
        # Wait for future to complete
        final_state = await future
            
        # Get result
        try:
            # Handle CSV saving and preview
            query_result = final_state.get("query_result")
            if query_result and isinstance(query_result, list):
                 # Save full result to CSV
                 save_result_to_csv(query_result)
                 
                 # Prepare preview (first 100)
                 preview_data = query_result[:100]
                 yield json.dumps({"type": "data", "content": preview_data}, default=custom_json_serializer) + "\n"
            else:
                 # Clear file if no result
                 save_result_to_csv([])

            # Yield generated SQL for the 'Query' tab
            generated_sql = final_state.get("generated_sql")
            if generated_sql:
                yield json.dumps({"type": "query", "content": generated_sql}, default=custom_json_serializer) + "\n"

            final_answer = final_state.get("final_answer", "No answer generated.")
            yield json.dumps({"type": "result", "content": final_answer}, default=custom_json_serializer) + "\n"

        except Exception as e:
            logger.error(f"Error processing graph result: {str(e)}")
            yield json.dumps({"type": "error", "content": f"Failed to process graph result: {str(e)}"}, default=custom_json_serializer) + "\n"

    except Exception as e:
        logger.error(f"Graph execution failed: {str(e)}")
        yield json.dumps({"type": "error", "content": f"Graph execution failed: {str(e)}"}, default=custom_json_serializer) + "\n"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        process_graph_stream(request), 
        media_type="application/x-ndjson"
    )

@app.get("/download")
async def download_endpoint():
    if os.path.exists(LATEST_RESULT_FILE):
        return FileResponse(LATEST_RESULT_FILE, media_type='text/csv', filename="query_result.csv")
    raise HTTPException(status_code=404, detail="No result file found")

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    # Using uvicorn run normally would show logs in console unless we pass log_config=None or similar, 
    # but our setup_logging clears handlers on 'uvicorn' loggers too.
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
