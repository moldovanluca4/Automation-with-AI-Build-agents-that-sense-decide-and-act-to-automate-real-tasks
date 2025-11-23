#IMPORTS 
#sqlite3 built in dbms allows the script to read the list of websites and visit them
#tldextract is a life saver tools bcs can easily spot the diff between the suffix and the domain of a website(if we have something like proarena.co.ro spots the domain proarena and the suffix .co.ro)
#time used for time sleep pause the script mimic human like behaviour
#re used in case we have to accept cookies
#and playwright sed for web scraping

import sqlite3
import tldextract
import time
import re  
from playwright.sync_api import sync_playwright

#DB config

db = "companies_url.db"
input_table = "google_search_result"
output_table = "companies_url"

#good to avoid pages we dont need - in order to keep the data clean
ignore_this_domains = {
    "facebook", "twitter", "linkedin", "instagram", "youtube", "google", 
    "wikipedia", "reddit", "pinterest", "apple", "adobe", "microsoft",
    "wordpress", "medium", "cloudflare", "amazon", "github", "glassdoor",
    "capterra", "g2", "trustradius" 
}


#we create another table that will now contain the actual websites and the url from which we can extract further data in the next steps
def init_db():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {output_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_blog_url TEXT,
            company_name TEXT,
            company_url TEXT UNIQUE,
            status TEXT DEFAULT 'new'
        )
    """)
    conn.commit()
    return conn


def extract_companies():
    conn = init_db()
    cursor = conn.cursor()
    
    
    try:
        print(f"Check '{input_table}' for unprocessed links")                                            #in the previous script we also had column in the table with "not processed yet" attribute
        cursor.execute(f"SELECT id, url FROM {input_table} WHERE status = 'not processed yet'")          #this attribute comes handy in this step since we have to keep track which website we visited and which not
        blogs_to_visit = cursor.fetchall()                                                               #for ex if something happens a compuer crash internet problem etc when running the script again you wont overwrite already written data which was processed already
    except Exception as e:
        print(f"db error: {e}")
        print(f"Does '{input_table}' exists in '{db}' ? check this")
        return

    if not blogs_to_visit:
        print("nothing to visit")
        return

    print(f"Found {len(blogs_to_visit)} websites for processing")

    with sync_playwright() as p:
        #we use a so called disguise  to trick websites that we are an actual user bcs playwright itself introduces himself as a bot
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"          #this way we can bypas basic firewalls easily
        )
        page = context.new_page()

#only now we begin visiting each website we saved in the sqlite db from the previous step 
        for blog in blogs_to_visit:
            blog_id = blog[0]
            blog_url = blog[1]
            print(f"In work is -> {blog_url}")
            
            try:
                page.goto(blog_url, timeout=60000, wait_until="domcontentloaded")   #we wait until the html is ready but we dont wait for adds or tracking pixels to load we dont need to wait for that and that a tradeoff in scraping speed

#Handling Cookies and Lazy loading              
                try:
                    #cookie accepter - and here re coms in hand because it mimics the comfirmation button pattern for cookies
                    cookie_btn = page.get_by_role("button", name=re.compile(r"(accept|agree|allow|okay|got it|alle|akzeptieren)", re.IGNORECASE))
                    if cookie_btn.count() > 0 and cookie_btn.first.is_visible():
                        print("I accept the cookies(unfortunately)")
                        cookie_btn.first.click()
                        time.sleep(2)
                    else:
                        print("There are no cookies here(Yeeeessss)")
                except Exception as cookie_err:
                    print(f"cookie error: {cookie_err}")

                #for lazy loading sites we use this approach bcs in some cases websites dont load images or footer links until you scroll at the end of the homepage this means for us a potential data loss which we dont want
                print("Scrolling")
                for _ in range(3):
                    page.mouse.wheel(0, 3000)
                    time.sleep(1)

                #extracting the links
                blog_domain = tldextract.extract(blog_url).domain
                links = page.locator("a").all()
                print(f"So far{len(links)} links")

                saved_count = 0
                
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        text = link.inner_text().strip()
                        
                        if not href or not text:
                            continue

                        
                        if href.startswith("/"):
                            href = blog_url + href
                            
                        
                        domain_info = tldextract.extract(href)
                        domain = domain_info.domain
                        
                        #filter 1 - getting external links only
                        if domain == blog_domain:
                            continue

                        #filter 2 - ignoring unwanted links
                        if domain in ignore_this_domains:
                            continue 

                        #filter 3 - we make sure we get only company names not any other unwanted data        
                        if len(text.split()) > 5:
                            continue 

                        #filter 4 - garbage check making sure we filter out buttons or icons
                        if len(text) < 3:
                            continue 

                        #saving the data found so far
                        try:
                            cursor.execute(f"""
                                INSERT INTO {output_table} (source_blog_url, company_name, company_url) 
                                VALUES (?, ?, ?)
                            """, (blog_url, text, href))
                            conn.commit()
                            saved_count += 1
                            print(f"Saved: {text} ({domain})")
                        except sqlite3.IntegrityError:
                            print(f"Duplicates: {text}") 
                            pass

                    except:
                        continue

                #we mark a process - we change in the previous table the status of the website from "not processed yet" to "done" which is a trivial action keepimg track of what has been processed even for small or large datasets 
                cursor.execute(f"UPDATE {input_table} SET status = 'done' WHERE id = ?", (blog_id,))
                conn.commit()
                print(f"Found {saved_count} companies")

            except Exception as e:
                print(f"Error while accessing this page: {e}")
                cursor.execute(f"UPDATE {input_table} SET status = 'error' WHERE id = ?", (blog_id,))
                conn.commit()

        browser.close()
    conn.close()

if __name__ == "__main__":
    extract_companies()