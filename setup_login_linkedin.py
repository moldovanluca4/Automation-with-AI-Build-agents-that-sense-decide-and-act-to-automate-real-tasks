#IMPORTS
#getpass allows the user to type the email and the password without appearing on the terminal - a good security practice
#playwright used for scraping

import getpass
from playwright.sync_api import sync_playwright

def save_login_state():
    #user input
    email = getpass.getpass("Enter e-mail(for Linkedin):")
    password = getpass.getpass("Enter password(for Linkedin): ") 

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False) 
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.linkedin.com/login")

        try:
            page.fill('#username', email)
            page.fill('#password', password)
            page.click('button[type="submit"]')
        except Exception as e:
            print(f"Auto-fill failed (page might have changed): {e}")
            print("Please type credentials manually in the browser window.")
        input(">>> Press ENTER in this terminal AFTER you are fully logged in...")
        #storing the cookies
        context.storage_state(path="linkedin_state.json")
        #this step is essential because evrytime we run a bot and load the specific file the browser remembers we logged in before and we can safely bypas captchas
        
        browser.close()

if __name__ == "__main__":
    save_login_state()


#this code can be used as a template for multiple resources like linkedin 
#we skipped selecting duckduckgo also because of efficiency and also bcs of the ads and the risk of receiving garbage data