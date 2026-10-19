import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))
from settings import DATABASE_PATH
import sqlite3

db = DATABASE_PATH

def clean_slate():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS companies_reddit")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    clean_slate()