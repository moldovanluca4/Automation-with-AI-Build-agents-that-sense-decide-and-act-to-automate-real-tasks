#IMPORTS
#playwright - browser automation tool
#sqlite3 - manage embedded db

import sqlite3
import time
import random
import os
from playwright.sync_api import sync_playwright

#the main goal of this script is to look inside each company linked page - theres some valuable data that we can obtain 100% from the linkedin profiles
#from linkedin profiles we always can get info about the headquarters, company size, maybe founding year, maybe products and also the industry

db = "companies_url.db"
input_table = "companies_url"       
output_table = "companies_details"   
cookie_file = "linkedin_state.json"              #we have json file that contains the saved login cookies - allows user to login easily                         

def init_db():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {output_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            linkedin_url TEXT UNIQUE,
            industry TEXT,
            company_size TEXT,
            headquarters TEXT,
            founded_year TEXT,
            specialties TEXT,
            products TEXT,
            website TEXT,
            description TEXT
        )
    """)
    conn.commit()
    return conn

def get_companies():
    conn = init_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{input_table}';")
        if not cursor.fetchone(): return []
        cursor.execute(f"SELECT company_name FROM {input_table}")
        rows = cursor.fetchall()
        return list(set([r[0].strip() for r in rows if r[0]]))
    except: return []
    finally: conn.close()

def human_behaviour():
    time.sleep(random.uniform(3.0, 6.0))

#linkedin is throwing popups - the one i had problems while writing this code was the one saying "do you allow people to see that you visited theyre profiles"(or something like that)
#and the options for that were allow and dont allow - and the beginning we collected really few data due to that popup cause for one in three pages the popup appears and the code used to skip pages bcs of that
def handle_popups(page):
    try:
        dont_allow_btn = page.locator("button").filter(has_text="Don't allow").first
        if dont_allow_btn.is_visible():
            dont_allow_btn.click()
            time.sleep(0.5)
    except: pass
    try:
        msg_close = page.locator("header button[type='button']").filter(has_text="Close your conversation").first
        if msg_close.is_visible(): msg_close.click()
    except: pass

#extracts specific data based on the defined labels
#it levarages the definition lists from html
def get_grid_value(page, label_text):
    try:
        locator = page.locator(f"//dt[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label_text.lower()}')]/following-sibling::dd[1]")
        if locator.count() > 0:
            return locator.first.inner_text().strip()
    except: pass
    return None

#when we enter a company page on linkedin this function reads the html
#we look at the currently open linkedin page and fill the dictionary with the piece of data needed(in case we find it)
def extract_details(page, company_name, url):
    data = {
        "company_name": company_name,
        "linkedin_url": url,
        "industry": "none",
        "company_size": "none",
        "headquarters": "none",
        "founded_year": "none",
        "specialties": "none",
        "products": "none",
        "website": "none",
        "description": "none"
    }
  
    try:
        data["description"] = page.locator("section.artdeco-card p.break-words").first.inner_text().strip()
    except: pass

  
    try:
        top_items = page.locator(".org-top-card-summary-info-list__info-item").all_inner_texts()
        
        for item in top_items:
            text = item.strip()
            lower_text = text.lower()
            
            if data["industry"] == "none" and "employee" not in lower_text and "follower" not in lower_text:
                if "," not in text:
                    data["industry"] = text
            
          
            if "employee" in lower_text:
                data["company_size"] = text
            
            if "follower" not in lower_text and "employee" not in lower_text:
                if "," in text or (data["industry"] != "none" and text != data["industry"]):
                    data["headquarters"] = text

    except Exception as e:
        pass

    try:
        product_section = page.locator("section").filter(has_text="Products").first
        if product_section.count() > 0:
            product_items = product_section.locator("li .t-bold").all_inner_texts()
            if product_items:
                clean_products = [p.strip() for p in product_items if p.strip()]
                data["products"] = ", ".join(clean_products)
    except: pass


    grid_hq = get_grid_value(page, "Headquarters")
    if grid_hq: data["headquarters"] = grid_hq
    
    grid_founded = get_grid_value(page, "Founded")
    if grid_founded: data["founded_year"] = grid_founded
    
    grid_specs = get_grid_value(page, "Specialties")
    if grid_specs: data["specialties"] = grid_specs
    
    grid_size = get_grid_value(page, "Company size")
    if grid_size: data["company_size"] = grid_size.split('\n')[0] 

   
    data["website"] = get_grid_value(page, "Website")
    if not data["website"]:
         try:
            website_loc = page.locator("a").filter(has_text="Visit website").first
            if website_loc.count() > 0:
                data["website"] = website_loc.get_attribute("href")
         except: pass

    return data

def save_to_db(data):
    conn = init_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            INSERT OR REPLACE INTO {output_table} 
            (company_name, linkedin_url, industry, company_size, headquarters, founded_year, specialties, products, website, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["company_name"], data["linkedin_url"], data["industry"], 
            data["company_size"], data["headquarters"], data["founded_year"], 
            data["specialties"], data["products"], data["website"], data["description"]
        ))
        conn.commit()
    except Exception as e:
        print(f"db error: {e}")
    finally:
        conn.close()

#start the browser, search each company, enter linkedin profile, search for the wanted info
def main_scraper():
    if not os.path.exists(cookie_file):
        print(f"error = {cookie_file} - run setup_login_linkedin")
        return

    company_names = get_companies()
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, slow_mo=50)
        context = browser.new_context(storage_state=cookie_file)
        page = context.new_page()

        for company in company_names:
            try:
                page.goto("https://duckduckgo.com")
                page.locator('input[name="q"]').fill(f"{company} linkedin")
                page.keyboard.press("Enter")
                
                try:
                    page.wait_for_selector("article h2 a", timeout=5000)
                except:
                    print("timeout")
                    continue

                results = page.locator("article h2 a").all()
                valid_url = None
                for res in results:
                    url = res.get_attribute("href")
                    if url and ("linkedin.com/company/" in url or "linkedin.com/school/" in url):
                        valid_url = url
                        break
                
                if not valid_url:
                    print("no url found")
                    continue
                
                if valid_url.endswith("/"): valid_url = valid_url[:-1]
                about_url = f"{valid_url}/about/"
                page.goto(about_url, timeout=60000)
                
                time.sleep(2)
                handle_popups(page)
                human_behaviour()

                if "login" in page.url or "authwall" in page.url:
                    print("auth wall")
                    break
                
                if "Page not found" in page.title():
                    print("page not found")
                    page.goto(valid_url, timeout=60000)
                    time.sleep(2)
                    handle_popups(page)

                details = extract_details(page, company, valid_url)
                save_to_db(details)

            except Exception as e:
                print(f"Error processing {company}: {e}")
                try: page = context.new_page()
                except: pass

        browser.close()

if __name__ == "__main__":
    main_scraper()