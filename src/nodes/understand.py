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

def understand_query(state: AgentState) -> AgentState:
    """
    Extracts structured intent from the user query.
    """
    user_query = state["user_query"]
    
    llm = ChatOpenAI(temperature=0, model="gpt-4o")

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at extracting structured intent from natural language queries. "
                "Output your response as a JSON object with the following keys:\n"
                "- intent_type: (e.g., selection, aggregation, count, etc.)\n"
                "- metrics: List of metrics mentioned (e.g., salary, employee count)\n"
                "- dimensions: List of dimensions mentioned (e.g., department, name)\n"
                "- filters: Dictionary of filters mentioned (e.g., {{'name': 'Alice'}})\n"
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

    print("\n--- NODE: Understand_Query ---")
    print(f"User Query: {user_query}")
    print(f"Structured Intent: {json.dumps(intent, indent=2)}")

    return {**state, "intent": intent}