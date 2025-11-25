import sqlite3
import re
import os


db = "companies_url.db"

table_name = "companies_discussions" 

#keep the popular forums
good_domains= [
    "reddit.com", "quora.com", "ycombinator.com", "stackexchange.com", "stackoverflow.com", 
    "g2.com", "capterra.com", "trustpilot.com", "trustradius.com", 
    "glassdoor.com", "bbb.org", "complaintsboard.com", "consumeraffairs.com", "pissedconsumer.com", 
    "ripoffreport.com", "peerspot.com", "vossity.com", "justuseapp.com", "softwareadvice.com",
    "getapp.com", "slashdot.org"
]

#common url patterns for forums or discussion pages
good_url_patterns = [
    "/forum/", "/community/", "/discuss/", 
    "/threads/", "/reviews/"
]

#helper fuction to decide which url respects our criteria
#the first filter checks if the selected url is not a blog or a news page since we want only forums at this point - if we encoutered a new website we mark it false and will be removed later
#if the url passes the first filter we check after if it matches the good domains and the good url patterns - if not we return false 
def should_keep_url(url):
    url_lower = url.lower()        #we solve a corner case that has been problematic and can cause valuable data loss - for ex we ensure that Reddit.com and reddit.com are the same

    if any(x in url_lower for x in ["/blog/", "/news/", "/article/", "/pulse/", "npr.org", "forbes.com", "medium.com"]):       
        return False
   
    for domain in good_domains:
        if domain in url_lower:
            return True
  
    for pattern in good_url_patterns:
        if pattern in url_lower:
            return True

    return False

#we will apply the helper function here so we can actually modify the database content(using the filter) 
#we fetch from the database only the forum url and the id of the tuple in order to process them
#we initialize some counters to see how many urls were kept and how many were discarded its good to know so we can approximate the data loss(make a statistic maybe to see whats the percentage of good data per some data sets of x companies)
#after that we run the filtering loop that goes trough every single tuple and runs the helper function for every url
#if the function returns false the tuple is being deleted from the table
#we save the new version of the database but theres a problem - we had deleted tuples from the table so that means there are high chances to have gaps in between the tuple
#we can solve this gaps by running the VACUUM command that rebuilds the table and removes the gaps - good for efficiency and reducing the file size on the memory
def filter_database(): 
    if not os.path.exists(db):
        print("error - no db found")
        return

    conn = sqlite3.connect(db)
    cursor = conn.cursor()

  
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
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


#theres a potential efficiency issue which I tried to analyze - filtering loop is good for smaller tables
#for ex if we have to delete 20000 tuples from the table since we run the delete inside a loop the code will send 20000 separate requests to delete - which is slow and not scalable
