#IMPORTS
#sqlite3 - interacting with the local db
#time and random - make random pauses to mimic human like movement 

from playwright.sync_api import sync_playwright
import sqlite3
import time
import random

db = "companies_url.db"
table = "companies_linkedin"

def init_db():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table}(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                linkedin_url TEXT UNIQUE,
                status TEXT DEFAULT 'not processed yet'
                )
                """)
    conn.commit()
    return conn

#the point is to search only the companies we got from the first part so the ones we already have in our db
#we extract them and store them in a list that we can use further in this code
def get_company_names():
     conn = init_db()
     cursor = conn.cursor()
     cursor.execute("SELECT company_name FROM companies_url;")
     raw_data = cursor.fetchall()
     company_names = [row[0] for row in raw_data]
     conn.close()
     return company_names

#collect and store linkedin profiles
def scrape_and_save_linkedin():
    company_names = get_company_names()
    print(f"{len(company_names)} companies found")

    conn = init_db()
    cursor = conn.cursor()

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, slow_mo=50)
        page = browser.new_page()

#loop trough the company array containing company names
        for company in company_names:
            try:
                search_term = f"{company} linkedin"
                
                page.goto("https://duckduckgo.com")
                page.locator('input[name="q"]').fill(search_term)
                page.keyboard.press("Enter")

                try: 
                    page.wait_for_selector("article h2 a", timeout=5000)
                except:
                    print("Timeout waiting for results")
                    continue

                results = page.locator("article h2 a").all()
                
                found = False
                for link in results:
                    url = link.get_attribute("href")
                    name = link.inner_text()

                    if url and "linkedin.com" in url:
                        try:
                            cursor.execute(f"INSERT INTO {table} (name, linkedin_url) VALUES (?,?)", (name, url))
                            conn.commit()
                            print(f"Saved: {url}")
                            found = True
                            break 
                        except sqlite3.IntegrityError:
                            print(f"Duplicate found: {name}")
                            found = True
                            break
                
                if not found:
                    print("No LinkedIn URL found")

                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"Error: {e}")

    conn.close()

if __name__ == "__main__":
    scrape_and_save_linkedin()

#here we used duckduckgo for few reasons - stable html easy, fewer blocks for robots, no cookies and neutral results since duckduckgo promises "unbiased results" (this is how they presented it)
