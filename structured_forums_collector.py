from playwright.sync_api import sync_playwright
import sqlite3
import time
import random
from urllib.parse import urlparse

#we use this script to search for pros and cons about the companies found previously
#we mainly search search for user experiences and thats why we target forums
#so inside this script we will focus on that - execute the search queries and retrieve the links from various forums


db = "companies_url.db"
source_table = "companies_url"
target_table = "companies_discussions"


#some key search queries that usually output forums 
search_variations = [
    'Why is {company} bad?',
    'Opinions on {company}?',
    '{company} user complaints', 
    'Why does {company} sucks?',
    'Why is {company} bad?',
    'Why is {company} a bad LMS?'
]

def init_db():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {target_table}(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                discussion_title TEXT,
                discussion_url TEXT UNIQUE,
                source_domain TEXT,
                search_query TEXT,
                status TEXT DEFAULT 'processed'
                )
                """)
    conn.commit()
    return conn

#retrieving the companies
def get_company_names():
     conn = init_db()
     cursor = conn.cursor()
     try:
         cursor.execute(f"SELECT company_name FROM {source_table}")
         raw_data = cursor.fetchall()
         return list(set([row[0] for row in raw_data if row[0]]))
     except: return []
     finally: conn.close()

def extract_domain(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return "unknown"

#for each company we will six search variations
#but we also collect the first two websites after each search query
def scrape_forums():
    company_names = get_company_names()
    conn = init_db()
    cursor = conn.cursor()

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, slow_mo=50)
        page = browser.new_page()

        for company in company_names:
            for query_template in search_variations:
                try:
                    search_term = query_template.format(company=company)
                    page.goto("https://duckduckgo.com")
                    page.locator('input[name="q"]').fill(search_term)
                    page.keyboard.press("Enter")

                    try: 
                        page.wait_for_selector("article h2 a", timeout=4000)
                    except:
                        print("no results :(")
                        continue

                    
                    all_results = page.locator("article h2 a").all()
                    
                    
                    top_two = all_results[:2] 
                    
                    for link in top_two:
                        url = link.get_attribute("href")
                        title = link.inner_text()
                        domain = extract_domain(url)
                        
                        if url and title:
                            try:
                                cursor.execute(f"""
                                    INSERT INTO {target_table} 
                                    (company_name, discussion_title, discussion_url, source_domain, search_query) 
                                    VALUES (?, ?, ?, ?, ?)
                                """, (company, title, url, domain, search_term))
                                conn.commit()
                            except sqlite3.IntegrityError:
                                pass
                    
                    time.sleep(random.uniform(1.5, 3.0))

                except Exception as e:
                    print(f"error on searching {search_term}: {e}")

    conn.close()
    browser.close()

if __name__ == "__main__":
    scrape_forums()