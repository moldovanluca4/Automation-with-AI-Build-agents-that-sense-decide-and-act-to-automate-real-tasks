#IMPORTS
#we went with synchronous version of playwright which allows the code to run step by step
#sqlite just for simplicity and easier to work locally

from playwright.sync_api import sync_playwright
import sqlite3

#DB CONFIG
#we define the database and table in which we store the results gathered after running thi script

db = "companies_url.db" 
table = "google_search_result"


#DB INITIALIZATION
#we connect to the sqlite db - if does not exists we create it
#we run an sql query to create the table inside the db if it doesnt exist yet
#sql schema details - id unique for each row inside the table to keep track of elements, name of the website found, and url of that specific website, and a status which will be used to keep track if we searched that specific website for companies and the urls
#basically in this step we gather resources - different blogs or any other websites containing information about the companies we want to get data from
#in this script we only gather those resources and in the next one we process thme

def init_db():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT UNIQUE,
            status TEXT DEFAULT 'not processed yet'
        )
    """)
    conn.commit()
    return conn

#SEARCH THE BROWSER
#in this step we perform the google search

def scrape_and_save():
    conn = init_db()
    cursor = conn.cursor()
    
    with sync_playwright() as p:                                                            #context manager - starts the playwright engine and shuts it down when is done
        browser = p.firefox.launch(headless=False, slow_mo=500)                             #we launch a firefox browser and we use headless flase so we can actually see the GUI which is good to see where does the context manager get stuck - maybe some cookies which he doesnt know how to accept since he was not programmed to accept them so overall good for debug, slow mo is also good to mimic human like movement in order to prevent being blocked by the search engine
        page = browser.new_page()                                                           #opens tab

        try:
            print("Message - running the search query")
            
            page.goto("https://duckduckgo.com")                                      #we us duckduckgo in order to avoid captchas
            
            search_term = "top LMS EdTech competitors list"                          #one of the search terms - but we can also use a data structure where we store more related search terms
            print(f"searching for {search_term}")
            
            page.locator('input[name="q"]').fill(search_term)                         #we locate the search bar type the search term and press enter to perform the search query
            page.keyboard.press("Enter")
            

#from this point onwards we should wait for the results as the search query was perfomed and indetify results and them fetch them and store them inside the sqlite
            try:
                page.wait_for_selector("li[data-layout='organic']", timeout=10000)                #to avoid being detected we pause the script until the results are fully loaded
            except:
                print("timeout")

            results = page.locator("li[data-layout='organic']").all()                           #after everything was fully loaded we push the results in a list
            print(f"found {len(results)} results")


            count = 0

#We use the following loop  to go trough each search result found and extract its name and url(website name and url)            
            for result in results:
                title_loc = result.locator("h2 a").first
                
                if title_loc.count() > 0:
                    name = title_loc.inner_text()
                    url = title_loc.get_attribute("href")
                    
#this step is crucial because we save to the database
                    if url and "http" in url:
                        try:
                            cursor.execute(f"INSERT INTO {table} (name, url) VALUES (?, ?)", (name, url))
                            count += 1
                            print(f"has been {name} added")
                        except sqlite3.IntegrityError:
                            print(f"skipped(duplicate): {name}")

            conn.commit()
            print(f"\nAdded {count} new websites to '{db}'")
            print("Next step = gather_companies_url script to process this websites")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
            conn.close()

if __name__ == "__main__":
    scrape_and_save()


#Also worth mentioning that the script only returns the best result basically what is considered on google to be the first page of results
#but here unlike google duckduckgo uses a "more results button" - so we only scarep what is visible immediately after the search
#but we can add a loop that clicks this "more results button" how many times we want(n times) before we start scraping


#heres a sketch of the logic behind the feature mentioned earlier

"""
pages_to_load = 3  

for i in range(pages_to_load):
    try:
        
        more_btn = page.locator("#more-results")
        
        if more_btn.is_visible():
            print(f"More results ({i+1}/{pages_to_load})")
            more_btn.click()
            page.wait_for_timeout(2500) 
        else:
            print("Error in locating the more results button")
            break
            
    except Exception as e:
        print(f"Error: {e}")
        break
        
results = page.locator("li[data-layout='organic']").all()
"""