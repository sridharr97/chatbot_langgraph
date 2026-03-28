import logging
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState

# Initialize logger
logger = logging.getLogger(__name__)

def generate_answer(state: AgentState, llm) -> AgentState:
    """
    Generates a natural language answer using the shared LLM.
    """
    query_result = state.get("query_result")
    user_query = state["user_query"]
    query_plan = state.get("query_plan", {})
    
    logger.info("\n--- NODE: Generate_Answer ---")
    
    # Check if we landed here because of a plan error
    if query_plan.get("error"):
        logger.info(f"Generating answer for plan error: {query_plan['error']}")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful assistant. The user asked a question that cannot be answered "
                    "using the available database. Explain politely why you cannot answer, "
                    "using the provided error details.",
                ),
                ("human", "User Query: {user_query}\nError details: {error}"),
            ]
        )
        chain = prompt | llm
        final_answer = chain.invoke({"user_query": user_query, "error": query_plan["error"]})
        logger.info(f"Final Answer: {final_answer.content}")
        return {**state, "final_answer": final_answer.content}

    # 1. SQL QA Agent Rule: Only pass data to LLM if <= 100 rows
    if query_result and isinstance(query_result, list) and len(query_result) > 100:
        msg = f"The data retrieved for your query contains {len(query_result)} records, which is more than 100 records and hence I cannot analyze it. You can view and download the output data in 'Output Data' tab."
        logger.info(f"Final Answer (Static): {msg}")
        return {**state, "final_answer": msg}

    if state["retry_count"] > 3 and not query_result:
        ans = "Unable to retrieve correct data after multiple attempts"
        logger.info(f"Final Answer: {ans}")
        return {**state, "final_answer": ans}

    # Create the prompt for successful data conversion
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at converting data into natural language.",
            ),
            ("human", "Here is the user query: {user_query}\n\nHere is the data: {data}\n\nPlease provide a natural language answer."),
        ]
    )

    # Create the chain
    chain = prompt | llm

    # Get the final answer
    final_answer = chain.invoke({"user_query": user_query, "data": query_result})
    
    logger.info(f"Final Answer: {final_answer.content}")

    return {**state, "final_answer": final_answer.content}
