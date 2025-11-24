import sqlite3

db = "companies_url.db"

def clean_slate():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS companies_details")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    clean_slate()