import sqlite3

def view_db():
    conn = sqlite3.connect('companies_url.db')
    cursor = conn.cursor()
    sql_query = "SELECT * FROM companies_details"
    
    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        print(f"Found {len(rows)} entries")
        for row in rows:
            print(row)
            
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        print(f"Tables found: {tables}")

    conn.close()

if __name__ == "__main__":
    view_db()