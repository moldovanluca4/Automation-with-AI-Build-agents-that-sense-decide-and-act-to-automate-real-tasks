import sqlite3
import re
import os


db = "companies_url.db"

table_name = "companies_discussions" 

good_domains= [
    "reddit.com", 
    "quora.com", 
    "ycombinator.com", 
    "stackexchange.com", 
    "stackoverflow.com", 
    "steamcommunity.com",
    "g2.com", 
    "capterra.com", 
    "trustpilot.com", 
    "trustradius.com", 
    "glassdoor.com", 
    "bbb.org", 
    "complaintsboard.com", 
    "consumeraffairs.com", 
    "pissedconsumer.com", 
    "ripoffreport.com",
    "peerspot.com",
    "vossity.com",
    "justuseapp.com",
    "softwareadvice.com",
    "getapp.com",
    "slashdot.org"
]

good_url_patterns = [
    "/forum/", 
    "/community/", 
    "/discuss/", 
    "/threads/", 
    "/reviews/"
]

def should_keep_url(url):
    url_lower = url.lower()

    
    if any(x in url_lower for x in ["/blog/", "/news/", "/article/", "/pulse/", "npr.org", "forbes.com", "medium.com"]):
        return False

   
    for domain in good_domains:
        if domain in url_lower:
            return True

    
    for pattern in good_url_patterns:
        if pattern in url_lower:
            return True

    return False

def filter_database(): 
    if not os.path.exists(db):
        print("error - no db found")
        return

    conn = sqlite3.connect(db)
    cursor = conn.cursor()

  
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        initial_count = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        print(f"error {table_name} not found, try another table name")
        return

    
    cursor.execute(f"SELECT id, discussion_url FROM {table_name}")
    rows = cursor.fetchall()
    
    deleted_count = 0
    kept_count = 0

    for row_id, url in rows:
        if should_keep_url(url):
            kept_count += 1
        else:
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (row_id,))
            deleted_count += 1

    
    conn.commit()
    conn.execute("VACUUM")

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    final_count = cursor.fetchone()[0]
    
    conn.close()

    
    print(f"deleted {deleted_count} rows")
    print(f"kept {kept_count} rows")
    print(f"db size: {final_count}")

if __name__ == "__main__":
    filter_database()