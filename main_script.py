import subprocess
import os
import sys
import time

#running the entire workflow, following the logical steps
#starts the browser, searches for each company, goes to the right place, extracts data, filters data
#the scripts that move data from the db to the googlesheet in order to be used inside the n8n is placed inside the gitignore for privacy reasons due to the API used

cookie_file = "linkedin_state.json"
login_helper = "setup_login_linkedin.py"

pipeline_steps = [
    {
        "name": "Gather Search Results",
        "script": "structure_data_collector.py",
        "desc": "Scraping DuckDuckGo for EdTech/LMS blogs"
    },
    {
        "name": "Extract Company URLs",
        "script": "gather_companies_url.py",
        "desc": "Visiting the collected blog - collecting company names and urls"
    },
    {
        "name": "Clean Company Data",
        "script": "data_filtering.py",
        "desc": "Filtering out garbage domains and data"
    },
    {
        "name": "Linkedin Scraper",
        "script": "scrape_linkedin_profiles.py",
        "desc": "Scraping Linkedin for valuable information - company size, hq, etc...",
        "requires_auth": True 
    },
    {
        "name": "Forum Scraper",
        "script": "structured_forums_collector.py",
        "desc": "Searching forums - searching for prons and cons"
    },
    {
        "name": "Filter Forums",
        "script": "data_filtering_forums.py",
        "desc": "Removing the garbage forums or non forums pages"
    },
    {
        "name": "Construct Main Table",
        "script": "constructing_main_table.py",
        "desc": "Creating a main table"
    }
]

def run_script(script_name):
    try:                                                                                #subprocess run is the standard way to run on program from inside another
        result = subprocess.run([sys.executable, "-u", script_name], check=True)      #equal with running python3 main_script.py, -u is the unbuffered mode used in debugging the scraping process mainly
        return True
    except subprocess.CalledProcessError as e:
        print(f"error {script_name}, exit code = {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"could not find {script_name}")
        return False

def check_linkedin_auth():
    if not os.path.exists(cookie_file):                                            #checking for the cookie file otherwise its a b
        print(f"\n authentification has failed {cookie_file} not found.")
    
        success = run_script(login_helper)
        
        if not success or not os.path.exists(cookie_file):
            print("linkedin setup failed no cookie file")
            return False
            
    return True

#in here we put everything together
def main():
    start_time = time.time()

    for step in pipeline_steps:
        print(f"\n[{step['name']}] {step['desc']}")
        
        if step.get("requires_auth"):
            if not check_linkedin_auth():
                print("skipped the linkedin scraping step, due to error authentificating")
                continue

        success = run_script(step["script"])                                                        #here we actually run the script
        
        if not success:                                                                             #stop everything if a step fails
            print(f"Pipeline has stopped at this step {step['name']}")
            sys.exit(1)
        
        time.sleep(1)                                                                           #pause between steps just in case 

    elapsed = time.time() - start_time                                                          #just out of curiosity to see how long does it take to run everything - in case optimizations are needed
    print(f"{elapsed}")

if __name__ == "__main__":
    main()