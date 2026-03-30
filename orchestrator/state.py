import operator
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
    # Using Annotated[..., operator.add] ensures that returning a list from a node
    # APPENDS to the existing list instead of overwriting it.
    sql_tool_results: Annotated[List[Dict[str, Any]], operator.add]

    # Track retries for the orchestrator level
    orchestrator_retry_count: int
