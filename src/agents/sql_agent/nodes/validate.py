import logging
from langchain_core.prompts import ChatPromptTemplate
from src.agents.sql_agent.state import AgentState

# Initialize logger
logger = logging.getLogger(__name__)

def validate_sql(state: AgentState, llm) -> AgentState:
    """
    Validates the generated SQL query using the shared LLM.
    """
    generated_sql = state["generated_sql"]
    
    if not generated_sql:
        return {**state, "sql_error": None}

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at validating SQL queries. If the query is valid, return 'valid'. Otherwise, return 'invalid' and the reason."
                "## Database-Specific Instructions"
                "The target database engine is **DuckDB**. When generating SQL:"
                "- Use DuckDB-compatible syntax only."
                "- For date arithmetic, use INTERVAL syntax (e.g., `CURRENT_DATE - INTERVAL '13 months`), NOT SQL Server-style. `DATEADD()` ."
                "- For string functions, use DuckDB-native functions (e.g., `LOWER()`, `CONCAT()`)."
                "- Do NOT use functions from SQL Server, PostgreSQL, or MySQL that are not supported in DuckDB."
            ),
            ("human", "Here is the SQL query: {sql_query}"),
        ]
    )

    chain = prompt | llm
    validation_result = chain.invoke({"sql_query": generated_sql})

    logger.info("\n--- NODE: Validate_SQL ---")
    logger.info(f"SQL to Validate: {generated_sql}")
    logger.info(f"SQL Validation Result: {validation_result.content}")

    if "valid" in validation_result.content.lower():
        return {**state, "sql_error": None}
    else:
        return {**state, "sql_error": validation_result.content}
