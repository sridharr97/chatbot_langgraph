import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os, getpass

from src.state import AgentState

load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")

# Enhanced schema with descriptions
SCHEMA = """
Table: employees
Description: Contains information about company employees, including their personal details, department, and salary.
Columns:
- id (INTEGER): Unique identifier for each employee.
- name (VARCHAR): The full name of the employee.
- department (VARCHAR): The department the employee works in (e.g., Engineering, Marketing, Sales).
- salary (INTEGER): The annual salary of the employee in USD.
"""

def plan_query(state: AgentState) -> AgentState:
    """
    Maps intent to the database schema and generates a structured plan.
    If the intent cannot be mapped to the schema, returns an error.
    """
    intent = state["intent"]
    
    llm = ChatOpenAI(temperature=0, model="gpt-4o")

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
                "- error: A string describing why the query cannot be fulfilled if the intent asks for fields or data not present in the schema. Set to null if no error.\n"
                "\n"
                "CRITICAL: If the intent asks for information (like 'geography', 'location', 'product', etc.) "
                "that is NOT explicitly present in the provided schema, do NOT attempt to map it to existing columns. "
                "Instead, populate the 'error' field with a clear explanation.\n"
                "Ensure the output is ONLY the JSON object.",
            ),
            ("human", "Intent: {intent}\n\nSchema:\n{schema}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke({"intent": json.dumps(intent), "schema": SCHEMA})
    
    # Clean output for safety
    content = response.content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    
    query_plan = json.loads(content)

    print("\n--- NODE: Plan_Query ---")
    if query_plan.get("error"):
        print(f"Plan Error: {query_plan['error']}")
    else:
        print(f"Structured Query Plan: {json.dumps(query_plan, indent=2)}")

    return {**state, "query_plan": query_plan}