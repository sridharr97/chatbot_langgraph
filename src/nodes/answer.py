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

def generate_answer(state: AgentState) -> AgentState:
    """
    Generates a natural language answer from the query result or error.
    """
    query_result = state.get("query_result")
    user_query = state["user_query"]
    query_plan = state.get("query_plan", {})
    
    print("\n--- NODE: Generate_Answer ---")
    
    # Check if we landed here because of a plan error
    if query_plan.get("error"):
        print(f"Generating answer for plan error: {query_plan['error']}")
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
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
        print(f"Final Answer: {final_answer.content}")
        return {**state, "final_answer": final_answer.content}

    print(f"Data for Answer: {query_result}")

    if state["retry_count"] > 3 and not query_result:
        ans = "Unable to retrieve correct data after multiple attempts"
        print(f"Final Answer: {ans}")
        return {**state, "final_answer": ans}

    # Initialize the model
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o",
    )

    # Create the prompt
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
    
    print(f"Final Answer: {final_answer.content}")

    return {**state, "final_answer": final_answer.content}