from typing import Annotated, Dict, List, Any, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class OrchestratorState(TypedDict):
    """
    State for the orchestrator agent.
    """
    # Standard conversational messages
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Separate field to preserve full structured tool outputs
    sql_tool_results: List[Dict[str, Any]]

    # Track retries for the orchestrator level
    orchestrator_retry_count: int
