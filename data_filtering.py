#IMPORTS 
#sqlite3 dbms
#pandas is a data analysis library alows us to filter the data
#urlib.parse is a library that dissects the URL
#tldextract identifies the main domain ignoring sub domains

import sqlite3
import pandas as pd
from urllib.parse import urlparse
import tldextract

#CONFIG

db = "companies_url.db"
table = "companies_url"

#if the script collected accidentally any of these buttons we rule them out, since its useless data for us
forbidden_names = [
    "Read more", "Learn More", "Visit their website", "Click here",
    "Login", "Sign in", "Register", "Contact", "About Us",
    "Privacy Policy", "Terms of Service", "Download", "AdChoices",
    "Reprints & Permissions", "Load More Startups", "Comments",
    "Start your learning journey now", "Download for free",
    "Watch list", "Resources"
]

#we rule out domains that are not corresponding to our task 
forbidden_domains = [
    "google", "facebook", "twitter", "linkedin", "instagram", 
    "youtube", "whatsapp", "wikipedia", "parsintl", "time", 
    "forbes", "reuters", "livemint", "youradchoices", 
    "truste", "magreprints", "renderforestsites", "geo.ema.gs"
]

def clean_database():
    conn = sqlite3.connect(db)

    try:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)            #for smaller datasets this approach of fetching the entire db at once in the computers RAM instead of fetching row by row is suitable bcs it makes the process faster and overall more efficient
        original_count = len(df)
        print(f"Loaded {original_count} entries")

        
        df = df[df['company_url'].str.startswith(('http://', 'https://'), na=False)]       #filter 1 - removes broken or non web links it deletes email links for ex or telephone links or other anchors
        
        #avoid bad patterns that we dont want
        pattern = '|'.join(forbidden_names)
        df = df[~df['company_name'].str.contains(pattern, case=False, na=False, regex=True)]

       #we want only the main domain that gives us the home page of each company
        def get_clean_domain_url(url):
            try:
                parsed = urlparse(url)
                return f"{parsed.scheme}://{parsed.netloc}"
            except:
                return None

        def get_domain_name(url):
            try:
                return tldextract.extract(url).domain
            except:
                return ""


        df['clean_url'] = df['company_url'].apply(get_clean_domain_url)
        df['domain_name'] = df['clean_url'].apply(get_domain_name)

        #filter 2 - extract the root domain and check if its forbidden or not
        df = df[~df['domain_name'].isin(forbidden_domains)]

        #we solve the duplication error since multpile websites contain the same companies so we want unique companies only (for ex we have 100 moodle.com we find the first and delete all the 99 that are left)
        df_clean = df.drop_duplicates(subset=['domain_name'], keep='first')

        #saving back to the db what is left after filtering 
        final_df = df_clean[['source_blog_url', 'company_name', 'clean_url', 'status']].copy()
        final_df = final_df.rename(columns={'clean_url': 'company_url'})
        final_df['status'] = 'new'
        final_df.to_sql(table, conn, if_exists='replace', index=False) #a brute force like approach since we drop the existing unfiltered table and create a new filtered table
        
        print(f"Initial entries{original_count}")
        print(f"We cleaned {len(final_df)} entries")
        print(f"we had removed {original_count - len(final_df)} garbage tuples")
        print("Quick look into the clean data:")
        print(final_df[['company_name', 'company_url']].head(10))

    except Exception as e:
        print(f"Error while cleaning(oops): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clean_database()