import sqlite3

db = "companies_url.db"

def combine_tables():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE main_table AS
        SELECT d.company_name, d.company_url, l.linkedin_url, l.company_size, l.headquarters, l.company_name
        FROM companies_url d
        LEFT JOIN companies_details l
        ON l.company_name = d.company_name
""")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    combine_tables()