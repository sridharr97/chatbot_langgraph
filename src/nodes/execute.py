from src.state import AgentState
from src.tools.duckdb_tool import execute_sql

def execute_sql_node(state: AgentState) -> AgentState:
    """
    Executes the SQL query using the DuckDB tool.
    """
    generated_sql = state["generated_sql"]
    
    print("\n--- NODE: Execute_SQL ---")
    print(f"Executing SQL: {generated_sql}")
    
    query_result = execute_sql(generated_sql)

    if isinstance(query_result, list) and query_result and "error" in query_result[0]:
        print(f"SQL Execution Error: {query_result[0]['error']}")
        return {**state, "sql_error": query_result[0]["error"], "query_result": None}
    else:
        print(f"SQL Execution Result: {query_result}")
        return {**state, "query_result": query_result, "sql_error": None}
