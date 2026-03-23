import json
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState

def generate_sql(state: AgentState, llm) -> AgentState:
    """
    Generates a SQL query using the shared LLM.
    """
    query_plan = state["query_plan"]
    
    # If there's an error in the plan, skip SQL generation
    if query_plan.get("error"):
        print("\n--- NODE: Generate_SQL ---")
        print(f"Skipping SQL generation due to plan error: {query_plan['error']}")
        return {**state, "generated_sql": None}
    
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
