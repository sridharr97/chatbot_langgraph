from typing import Literal

from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.understand import understand_query
from src.nodes.plan import plan_query
from src.nodes.generate import generate_sql
from src.nodes.validate import validate_sql
from src.nodes.execute import execute_sql_node
from src.nodes.check import check_result
from src.nodes.fix import fix_sql
from src.nodes.answer import generate_answer

def create_graph() -> StateGraph:
    """
    Creates the LangGraph agent.
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("Understand_Query", understand_query)
    graph.add_node("Plan_Query", plan_query)
    graph.add_node("Generate_SQL", generate_sql)
    graph.add_node("Validate_SQL", validate_sql)
    graph.add_node("Execute_SQL", execute_sql_node)
    graph.add_node("Check_Result", check_result)
    graph.add_node("Fix_SQL", fix_sql)
    graph.add_node("Generate_Answer", generate_answer)

    # Set entry point
    graph.set_entry_point("Understand_Query")

    # Add edges
    graph.add_edge("Understand_Query", "Plan_Query")

    # Conditional edges
    def plan_query_condition(state) -> Literal["Generate_SQL", "Generate_Answer"]:
        """
        Determines the next node based on whether the plan was successful.
        """
        print("\n--- EDGE: Plan_Query_Condition ---")
        if state["query_plan"].get("error"):
            print(f"Decision: Plan error detected: {state['query_plan']['error']}. Routing to Generate_Answer.")
            return "Generate_Answer"
        else:
            print("Decision: Plan is valid. Proceeding to Generate_SQL.")
            return "Generate_SQL"

    graph.add_conditional_edges(
        "Plan_Query",
        plan_query_condition,
    )

    graph.add_edge("Generate_SQL", "Validate_SQL")

    def validate_sql_condition(state) -> Literal["Execute_SQL", "Fix_SQL"]:
        """
        Determines the next node based on the state after validating SQL.
        """
        print("\n--- EDGE: Validate_SQL_Condition ---")
        if state["sql_error"] is None:
            print("Decision: SQL is valid. Proceeding to Execute_SQL.")
            return "Execute_SQL"
        else:
            print(f"Decision: SQL is invalid. Error: {state['sql_error']}. Proceeding to Fix_SQL.")
            return "Fix_SQL"

    def check_result_condition(state) -> Literal["Generate_Answer", "Fix_SQL"]:
        """
        Determines the next node based on the state after checking the SQL Executed result.
        """
        print("\n--- EDGE: Check_Result_Condition ---")
        if state["sql_error"] is None:
            print("Decision: Result is valid. Proceeding to Generate_Answer.")
            return "Generate_Answer"
        else:
            print(f"Decision: Result is invalid. Error: {state['sql_error']}. Proceeding to Fix_SQL.")
            return "Fix_SQL"

    def fix_sql_condition(state) -> Literal["Validate_SQL", "Generate_Answer"]:
        """
        Determines the next node based on the state after fixing SQL.
        """
        print("\n--- EDGE: Fix_SQL_Condition ---")
        if state["retry_count"] <= 3:
            print(f"Decision: Retry count ({state['retry_count']}) <= 3. Proceeding to Validate_SQL.")
            return "Validate_SQL"
        else:
            print(f"Decision: Retry count ({state['retry_count']}) > 3. Proceeding to Generate_Answer.")
            return "Generate_Answer"

    graph.add_conditional_edges(
        "Validate_SQL",
        validate_sql_condition,
    )
    graph.add_conditional_edges(
        "Check_Result",
        check_result_condition,
    )
    graph.add_conditional_edges(
        "Fix_SQL",
        fix_sql_condition,
    )

    graph.add_edge("Execute_SQL", "Check_Result")
    graph.add_edge("Generate_Answer", END)

    return graph.compile()
