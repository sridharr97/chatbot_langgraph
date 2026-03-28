import json
import logging
from langchain_core.prompts import ChatPromptTemplate
from src.agents.sql_agent.state import AgentState

# Initialize logger
logger = logging.getLogger(__name__)

def generate_sql(state: AgentState, llm) -> AgentState:
    """
    Generates a SQL query using the shared LLM.
    """
    query_plan = state["query_plan"]
    
    # If there's an error in the plan, skip SQL generation
    if query_plan.get("error"):
        logger.info("\n--- NODE: Generate_SQL ---")
        logger.info(f"Skipping SQL generation due to plan error: {query_plan['error']}")
        return {**state, "generated_sql": None}
    
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at generating clean SQL queries from structured JSON query plans. "
                "Output ONLY the SQL code. For string comparisons, use LOWER() to ensure case-insensitivity."
                "## Database-Specific Instructions"
                "The target database engine is **DuckDB**. When generating SQL:"
                "- Use DuckDB-compatible syntax only."
                "- For date arithmetic, use INTERVAL syntax (e.g., `CURRENT_DATE - INTERVAL '13 months`), NOT SQL Server-style. `DATEADD()` ."
                "- For string functions, use DuckDB-native functions (e.g., `LOWER()`, `CONCAT()`)."
                "- Do NOT use functions from SQL Server, PostgreSQL, or MySQL that are not supported in DuckDB."
            ),
            ("human", "Query Plan: {query_plan}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke({"query_plan": json.dumps(query_plan)})
    
    # Clean output
    sql = response.content.strip()
    if sql.startswith("```sql"):
        sql = sql.replace("```sql", "").replace("```", "").strip()

    logger.info("\n--- NODE: Generate_SQL ---")
    logger.info(f"Generated SQL: {sql}")

    return {**state, "generated_sql": sql}
