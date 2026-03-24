import os
import getpass
import logging
import asyncio
import json
import contextvars
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Import graph after logging setup might be safer, but let's just use the name
from src.graph import create_graph

# Load environment variables
load_dotenv()

ENV = os.getenv("ENV", "local")

# Context variable to hold the queue for the current request
log_queue_ctx = contextvars.ContextVar("log_queue", default=None)

# Global loop reference for the handler
_loop = None

class AsyncQueueHandler(logging.Handler):
    def emit(self, record):
        queue = log_queue_ctx.get()
        if queue and _loop:
            msg = self.format(record)
            try:
                _loop.call_soon_threadsafe(queue.put_nowait, msg)
            except Exception:
                pass

# Setup global logging for the src package
graph_logger = logging.getLogger("src")
graph_logger.setLevel(logging.INFO)
graph_logger.propagate = False # Don't log to console again

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
    # Attach the global handler once
    handler = AsyncQueueHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    graph_logger.addHandler(handler)

class ChatRequest(BaseModel):
    message: str

async def process_graph_stream(request: ChatRequest):
    """
    Generator that yields log events and the final result.
    """
    queue = asyncio.Queue()
    # Set the context variable for THIS request/coroutine
    token = log_queue_ctx.set(queue)
    
    # Capture the current context to propagate it to the thread
    ctx = contextvars.copy_context()
    
    try:
        # Run graph.invoke in a thread, ensuring context is propagated
        # We use ctx.run to execute the function within the captured context
        def run_with_context():
            return ctx.run(graph_app.invoke, {"user_query": request.message, "retry_count": 0})

        future = asyncio.get_running_loop().run_in_executor(None, run_with_context)
        
        while not future.done():
            # Wait for either a new log message or the future to complete
            queue_get_task = asyncio.create_task(queue.get())
            done, pending = await asyncio.wait(
                [queue_get_task, future], 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            if queue_get_task in done:
                log_msg = queue_get_task.result()
                yield json.dumps({"type": "log", "content": log_msg}) + "\n"
            else:
                queue_get_task.cancel()
            
            if future in done:
                break
        
        # Flush any remaining logs
        while not queue.empty():
            log_msg = await queue.get()
            yield json.dumps({"type": "log", "content": log_msg}) + "\n"
            
        # Get result
        try:
            final_state = await future
            final_answer = final_state.get("final_answer", "No answer generated.")
            yield json.dumps({"type": "result", "content": final_answer}) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "content": f"Graph execution failed: {str(e)}"}) + "\n"

    finally:
        log_queue_ctx.reset(token)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        process_graph_stream(request), 
        media_type="application/x-ndjson"
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
