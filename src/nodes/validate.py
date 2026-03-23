from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI # Changed from ChatGroq
from dotenv import load_dotenv
import os, getpass # Added getpass

from src.state import AgentState

load_dotenv()

# Function to set environment variables for OpenAI API key
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

# Set OpenAI API key from environment or prompt
_set_env("OPENAI_API_KEY")

def validate_sql(state: AgentState) -> AgentState:
    """
    Validates the generated SQL query.
    """
    generated_sql = state["generated_sql"]
    
    # Initialize the model
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o", # Using gpt-4o as a powerful default
    )

    # Create the prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at validating SQL queries. If the query is valid, return 'valid'. Otherwise, return 'invalid' and the reason.",
            ),
            ("human", "Here is the SQL query: {sql_query}"),
        ]
    )

    # Create the chain
    chain = prompt | llm

    # Get the validation result
    validation_result = chain.invoke({"sql_query": generated_sql})

    print("\n--- NODE: Validate_SQL ---")
    print(f"SQL to Validate: {generated_sql}")
    print(f"SQL Validation Result: {validation_result.content}")

    if "valid" in validation_result.content.lower():
        return {**state, "sql_error": None}
    else:
        return {**state, "sql_error": validation_result.content}