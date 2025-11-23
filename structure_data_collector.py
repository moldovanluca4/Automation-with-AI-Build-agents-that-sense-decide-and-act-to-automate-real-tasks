from playwright.sync_api import sync_playwright
import sqlite3
import time

def init_db():
    conn = sqlite3.connect("google_search_result.db")
    cursor = conn.cursor()
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS google_search_result(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT,
                   url TEXT UNIQUE,
                   status TEXT DEFAULT 'pending'
                   )
                   """)
    conn.commit()
    return conn



def scrape_and_save():
    conn = init_db()
    cursor = conn.cursor()
    
    with sync_playwright() as p:
        # Using DuckDuckGo logic here to be safe from blocks
        browser = p.firefox.launch(headless=False) 
        page = browser.new_page()

        try:
            print("Searching for competitors...")
            page.goto("https://duckduckgo.com")
            page.locator('input[name="q"]').fill("top LMS EdTech competitors list")
            page.keyboard.press("Enter")
            
            # Wait for results
            page.wait_for_selector("li[data-layout='organic']", timeout=5000)
            results = page.locator("li[data-layout='organic']").all()

            print(f"Found {len(results)} results. Saving to database...")

            count = 0
            for result in results:
                title_loc = result.locator("h2 a").first
                
                if title_loc.count() > 0:
                    name = title_loc.inner_text()
                    url = title_loc.get_attribute("href")
                    
                    if url and "http" in url:
                        try:
                            # Insert into DB. The UNIQUE constraint on 'url' prevents duplicates.
                            cursor.execute("INSERT INTO google_search_result (name, url) VALUES (?, ?)", (name, url))
                            count += 1
                            print(f"Saved: {name}")
                        except sqlite3.IntegrityError:
                            print(f"Skipped duplicate: {name}")

            conn.commit()
            print(f"\n--- SUCCESS: Added {count} new competitors to SQLite DB ---")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
            conn.close()

if __name__ == "__main__":
    scrape_and_save()