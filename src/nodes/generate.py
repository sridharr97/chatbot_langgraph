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

def generate_sql(state: AgentState) -> AgentState:
    """
    Generates a SQL query from a structured JSON query plan.
    """
    query_plan = state["query_plan"]
    
    llm = ChatOpenAI(temperature=0, model="gpt-4o")

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at generating clean SQL queries from structured JSON query plans. "
                "Output ONLY the SQL code. For string comparisons, use LOWER() to ensure case-insensitivity.",
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

    print("\n--- NODE: Generate_SQL ---")
    print(f"Generated SQL: {sql}")

    return {**state, "generated_sql": sql}