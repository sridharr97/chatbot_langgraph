import logging
from src.state import AgentState

# Initialize logger
logger = logging.getLogger(__name__)

def check_result(state: AgentState) -> AgentState:
    """
    Checks the result of the SQL query execution.
    """
    query_result = state["query_result"]
    sql_error = state["sql_error"]

    logger.info("\n--- NODE: Check_Result ---")

    if sql_error:
        logger.info(f"Check Result: Error detected - {sql_error}")
        return {**state, "sql_error": f"Execution Error: {sql_error}"}
    
    if not query_result:
        logger.info("Check Result: Empty result detected")
        return {**state, "sql_error": "Empty Result"}

    logger.info(f"Check Result: Valid result - {query_result}")
    return {**state, "sql_error": None}
