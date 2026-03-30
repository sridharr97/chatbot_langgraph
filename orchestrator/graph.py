import json
import logging
from typing import Dict, Any, List, Literal

from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from src.tools.sql_tool import sql_qa_tool
from src.tools.doc_tool import doc_qa_tool
from orchestrator.state import OrchestratorState

# Initialize logger
logger = logging.getLogger(__name__)

# --- 1. System Message ---
ORCHESTRATOR_SYSTEM_MESSAGE = SystemMessage(
    content="You are an orchestrator. If a question is complex or would require multiple tools, "
            "break it down into multiple queries and make the tool calls accordingly. "
            "Use the result of one query to inform the next.\n\n"
            "You have access to two tools:\n"
            "1. sql_query_tool: Use this for database related questions.\n"
            "2. doc_query_tool: Use this for document related questions."
)

# --- 2. Tool Wrapping ---

@tool
def sql_query_tool(user_query: str) -> Dict[str, Any]:
    """
    Use this tool to query the database. 
    Input should be a natural language question related to structured data.
    """
    logger.info(f"\n--- ORCHESTRATOR: Calling SQL QA Tool for query: '{user_query}' ---")
    return sql_qa_tool(user_query)

@tool
def doc_query_tool(user_query: str) -> Dict[str, Any]:
    """
    Use this tool to query internal documents. 
    Input should be a natural language question related to information available in documents.
    """
    logger.info(f"\n--- ORCHESTRATOR: Calling Doc QA Tool for query: '{user_query}' ---")
    return doc_qa_tool(user_query)


# --- 3. Graph Nodes ---

def call_model(state: OrchestratorState, config: Dict[str, Any]):
    """
    LLM node that decides whether to call tools or provide a final answer.
    """
    llm = config.get("configurable", {}).get("llm")
    if not llm:
        raise ValueError("LLM must be provided in the config under 'configurable.llm'")

    # Ensure system message is present at the start of conversation
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [ORCHESTRATOR_SYSTEM_MESSAGE] + messages

    # Enforcement: If retry limit reached, instruct LLM to stop calling tools
    if state.get("orchestrator_retry_count", 0) >= 2:
        logger.warning("Orchestrator retry limit (2) reached. Forcing final answer.")
        messages.append(SystemMessage(content="CRITICAL: You have reached the maximum retry limit. Do NOT call any more tools. Provide the best possible answer based on the information you already have."))

    response = llm.invoke(messages)

    # Force sequential execution: If LLM returns multiple tool calls, only keep the first one.
    if hasattr(response, "tool_calls") and len(response.tool_calls) > 1:
        logger.info(f"Orchestrator: Multiple tool calls detected ({len(response.tool_calls)}). Truncating to the first one for sequential execution.")
        response.tool_calls = response.tool_calls[:1]

    return {"messages": [response]}


def process_tool_outputs(state: OrchestratorState):
    """
    Node that processes ToolMessages to:
    1. Extract full structured tool results to state["sql_tool_results"].
    2. Summarize ToolMessage.content for the LLM context.
    3. Track orchestrator-level retries on error.
    """
    last_msg = state["messages"][-1]
    if not isinstance(last_msg, ToolMessage):
        return {}

    try:
        content = last_msg.content
        # Ensure content is a dictionary
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse ToolMessage content as JSON: {content[:100]}...")
                return {}

        if isinstance(content, dict):
            # Check for errors to increment retry count
            retry_increment = 0
            if content.get("status") == "error":
                retry_increment = 1
                logger.info(f"Orchestrator detected tool error. Incrementing retry count. New count: {state.get('orchestrator_retry_count', 0) + 1}")

            # Create a clean summary for the LLM context to avoid token bloat
            summary_content = {
                "status": content.get("status"),
                "answer": content.get("answer"),
                "error": content.get("error")
            }
            
            updated_tool_msg = ToolMessage(
                content=json.dumps(summary_content),
                tool_call_id=last_msg.tool_call_id,
                id=last_msg.id
            )
            
            # Prepare result dictionary. 
            # Note: sql_tool_results is now an Annotated list with operator.add reducer,
            # so we MUST return a list containing the new result.
            res = {
                "messages": [updated_tool_msg],
                "orchestrator_retry_count": state.get("orchestrator_retry_count", 0) + retry_increment,
                "sql_tool_results": [content] # Append the full result to the state
            }
            
            return res
            
    except Exception as e:
        logger.warning(f"Error in process_tool_outputs: {e}")
        
    return {}


# --- 4. Build the Orchestrator Graph ---

def create_orchestrator_graph(llm):
    """
    Creates and compiles the high-level orchestrator graph with persistent memory.
    """
    tools = [sql_query_tool, doc_query_tool]
    
    # We set parallel_tool_calls=False here to ensure the LLM only suggests one tool at a time.
    # This is safe here because tools ARE provided to the bind_tools call.
    try:
        llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
    except TypeError:
        # Fallback if the specific LLM class doesn't support this parameter
        logger.warning("LLM does not support parallel_tool_calls parameter. Falling back to default binding.")
        llm_with_tools = llm.bind_tools(tools)

    workflow = StateGraph(OrchestratorState)

    workflow.add_node("agent", lambda state, config: call_model(state, {**config, "configurable": {"llm": llm_with_tools}}))
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("process_outputs", process_tool_outputs)

    workflow.add_edge(START, "agent")
    
    def orchestrator_tools_condition(state: OrchestratorState):
        """
        Custom tools condition that also respects the retry limit.
        """
        if state.get("orchestrator_retry_count", 0) >= 2:
            return END
        return tools_condition(state)

    workflow.add_conditional_edges(
        "agent",
        orchestrator_tools_condition,
        {
            "tools": "tools",
            END: END
        }
    )

    workflow.add_edge("tools", "process_outputs")
    workflow.add_edge("process_outputs", "agent")

    # Initialize in-memory checkpointer for persistence
    checkpointer = MemorySaver()

    return workflow.compile(checkpointer=checkpointer)
