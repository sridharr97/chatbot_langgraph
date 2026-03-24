import json
import logging
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState

# Initialize logger
logger = logging.getLogger(__name__)

def fix_sql(state: AgentState, llm) -> AgentState:
    """
    Fixes the SQL query using the shared LLM.
    """
    generated_sql = state["generated_sql"]
    sql_error = state["sql_error"]
    query_plan = state["query_plan"]
    retry_count = state["retry_count"]
    
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at fixing SQL queries. You only return SQL code, and nothing else.",
            ),
            (
                "human", 
                "Original query plan: {query_plan}\n\n"
                "Broken SQL: {sql}\n\n"
                "Error: {error}\n\n"
                "Please fix the SQL query."
            ),
        ]
    )

    chain = prompt | llm
    fixed_sql = chain.invoke({
        "query_plan": json.dumps(query_plan), 
        "sql": generated_sql, 
        "error": sql_error
    })

    # Clean output
    sql = fixed_sql.content.strip()
    if sql.startswith("```sql"):
        sql = sql.replace("```sql", "").replace("```", "").strip()

    logger.info("\n--- NODE: Fix_SQL ---")
    logger.info(f"Broken SQL: {generated_sql}")
    logger.info(f"Error: {sql_error}")
    logger.info(f"Retry Count: {retry_count}")
    logger.info(f"Fixed SQL: {sql}")

    return {**state, "generated_sql": sql, "retry_count": retry_count + 1}
