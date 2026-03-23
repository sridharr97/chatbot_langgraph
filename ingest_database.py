
import duckdb



def setup_database():
    """
    Sets up the DuckDB database and populates it with sample data.
    """
    con = duckdb.connect('my_database.db')
    con.execute("CREATE OR REPLACE TABLE employees (id INTEGER, name VARCHAR, department VARCHAR, salary INTEGER)")
    con.execute("INSERT INTO employees VALUES (1, 'Alice', 'Engineering', 100000)")
    con.execute("INSERT INTO employees VALUES (2, 'Bob', 'Engineering', 120000)")
    con.execute("INSERT INTO employees VALUES (3, 'Charlie', 'Marketing', 90000)")
    con.execute("INSERT INTO employees VALUES (4, 'David', 'Sales', 80000)")
    con.execute("INSERT INTO employees VALUES (5, 'Eve', 'Sales', 85000)")
    con.close()