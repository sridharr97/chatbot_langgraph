import json
import logging
from langchain_core.prompts import ChatPromptTemplate
from src.agents.sql_agent.state import AgentState

# Initialize logger
logger = logging.getLogger(__name__)

def understand_query(state: AgentState, llm) -> AgentState:
    """
    Extracts structured intent from the user query using the shared LLM.
    """
    user_query = state["user_query"]
    
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at extracting structured intent from natural language queries. "
                "Output your response as a JSON object with the following keys:\n"
                "- intent_type: (e.g., selection, aggregation, count, etc.)\n"
                "- metrics: List of metrics mentioned.\n"
                "- dimensions: List of dimensions mentioned.\n"
                "- filters: Dictionary of filters mentioned (e.g., {{'name': 'Alice'}})\n"
                "- sorting: List of fields to sort by (if mentioned)\n"
                "- joins: List of any implied joins (if mentioned)\n"
                "- limit: An integer specifying the maximum number of rows to return (if applicable)\n"
                "Ensure the output is ONLY the JSON object.",
            ),
            ("human", "Query: {user_query}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke({"user_query": user_query})
    
    # Clean output for safety
    content = response.content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    
    intent = json.loads(content)

    logger.info("\n--- NODE: Understand_Query ---")
    logger.info(f"User Query: {user_query}")
    logger.info(f"Structured Intent: {json.dumps(intent, indent=2)}")

    return {**state, "intent": intent}
