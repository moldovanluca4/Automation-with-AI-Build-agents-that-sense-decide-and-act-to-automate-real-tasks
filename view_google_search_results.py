import sqlite3


def view_db():
    conn = sqlite3.connect("google_search_result.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM google_search_result")
    rows = cursor.fetchall()

    print(f"DB content {len(rows)} entries")


    conn.close()

if __name__ == "__main__":
    view_db()