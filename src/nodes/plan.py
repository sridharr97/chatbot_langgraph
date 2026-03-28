import json
import os
import logging
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState

# Initialize logger
logger = logging.getLogger(__name__)

# Load schema from JSON file
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "resources", "schema.json")
with open(SCHEMA_PATH, "r") as f:
    SCHEMA = json.load(f)

def plan_query(state: AgentState, llm) -> AgentState:
    """
    Maps intent to the database schema using the shared LLM and a structured JSON schema.
    """
    intent = state["intent"]
    
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at mapping structured intents to a database schema. "
                "Output your response as a JSON object with the following keys:\n"
                "- tables: List of tables required\n"
                "- joins: List of join conditions (if multiple tables)\n"
                "- columns: List of columns to select\n"
                "- aggregations: List of aggregations (if needed)\n"
                "- filters: List of filter conditions in SQL-like syntax\n"
                "- group_by: List of columns for grouping\n"
                "- order_by: List of columns to sort the results by. ALWAYS include at least one column to ensure consistent results.\n"
                "- limit: An integer specifying the maximum number of rows to return (if applicable)\n"
                "- error: A string describing why the query cannot be fulfilled if the intent asks for fields or data not present in the schema. Set to null if no error.\n"
                "\n"
                "CRITICAL: Try to map the intent to the closest matching fields in the schema. If the intent asks for information "
                "that is NOT present in the provided schema, do NOT attempt to map it to existing columns. "
                "Instead, populate the 'error' field with a clear explanation.\n"
                "\n"
                "MANDATORY: Your plan MUST always include an 'order_by' field to ensure the output data is sorted. Choose the most relevant field (e.g., a date, an ID, a value, or a primary category) for sorting.\n"
                "Ensure the output is ONLY the JSON object.",
            ),
            ("human", "Intent: {intent}\n\nSchema:\n{schema}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke({"intent": json.dumps(intent), "schema": json.dumps(SCHEMA, indent=2)})
    
    # Clean output for safety
    content = response.content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    
    query_plan = json.loads(content)

    logger.info("\n--- NODE: Plan_Query ---")
    if query_plan.get("error"):
        logger.info(f"Plan Error: {query_plan['error']}")
    else:
        logger.info(f"Structured Query Plan: {json.dumps(query_plan, indent=2)}")

    return {**state, "query_plan": query_plan}
