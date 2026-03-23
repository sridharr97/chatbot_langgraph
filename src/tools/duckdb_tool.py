import duckdb
from typing import List, Dict, Any
import re

def extract_sql_from_markdown(text: str) -> str:
    """
    Extracts a SQL query from a markdown code block.
    """
    match = re.search(r"```sql\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def execute_sql(sql_query: str) -> List[Dict[str, Any]]:
    """
    Executes a SQL query on the DuckDB database and returns the result.
    It automatically extracts SQL from markdown code blocks.

    Args:
        sql_query (str): The SQL query to execute (can be wrapped in markdown).

    Returns:
        List[Dict[str, Any]]: The result of the query execution.
    """
    # Extract SQL from markdown if present
    sql_query = extract_sql_from_markdown(sql_query)

    try:
        con = duckdb.connect('my_database.db')
        result = con.execute(sql_query).fetchdf().to_dict(orient='records')
        con.close()
        return result
    except Exception as e:
        return [{"error": str(e)}]
