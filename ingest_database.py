import duckdb
import os

def ingest_data():
    """
    Creates a sample DuckDB database and populates it with mock data.
    """
    db_path = "src/resources/my_database.db"
    
    # Remove existing db if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        
    con = duckdb.connect(db_path)
    
    # Create sample table
    con.execute("""
        CREATE TABLE employees (
            id INTEGER,
            name VARCHAR,
            department VARCHAR,
            salary INTEGER
        )
    """)
    
    # Insert mock data
    con.execute("INSERT INTO employees VALUES (1, 'Alice', 'Engineering', 100000)")
    con.execute("INSERT INTO employees VALUES (2, 'Bob', 'Sales', 80000)")
    con.execute("INSERT INTO employees VALUES (3, 'Charlie', 'Engineering', 120000)")
    con.execute("INSERT INTO employees VALUES (4, 'David', 'Marketing', 90000)")
    con.execute("INSERT INTO employees VALUES (5, 'Eve', 'Sales', 85000)")
    
    con.close()
    print(f"Database created successfully at {db_path}")

if __name__ == "__main__":
    ingest_data()
