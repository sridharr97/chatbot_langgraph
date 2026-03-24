import logging
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState

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
                "You are an expert at validating SQL queries. If the query is valid, return 'valid'. Otherwise, return 'invalid' and the reason.",
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
