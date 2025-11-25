# Automation-with-AI-Build-agents-that-sense-decide-and-act-to-automate-real-tasks

## Hackathon proj - Market Research Automation Agent

A modular Python-based automation suite designed to "sense, decide, and act" to perform comprehensive market research. This project automates the discovery of competitor companies (specifically in the EdTech/LMS space), scrapes their details from LinkedIn, and gathers public sentiment from forum discussions.

## Contributors:

- Moldovan Luca

- Moldoveanu Virgiliu Stefan

- Manolescu Neacsu Andrei


## Project Overview

This project is built as a pipeline of scripts that handle specific stages of the data gathering process:

Competitor Discovery: We first search for blogs and articles related to competitors in the EdTech LMS field. It saves these blogs and scrapes them to extract a list of company names and URLs, which serves as the main dataset.

LinkedIn: The agent then locates the LinkedIn profile for each company in the dataset. These profiles are scraped to extract valuable structured information such as Company Size, Headquarters, etc. Information which will be used to create the wiki style page for each company.

Forums Research: Finally,we search specifically for forums to extract pros and cons about each company. This implements a strong market research strategy by aggregating authentic user experiences and complaints to assess competitor reputation.

## Arhitecture and Workflow

The project is divided into distinct stages. Run the scripts in the following order to build the dataset:

### Phase 1: Discovery 

These scripts are responsible for finding and fetching initial data from the web.

structure_data_collector.py: Initiates the process by searching DuckDuckGo for competitor lists (search_term = "Top LMS companies") and storing the results.

gather_companies_url.py: Visits the blogs found in the previous step to extract specific company names and URLs. It filters out social media or garbage links to find the actual company homepages.

### Phase 2: Cleaning Data

These scripts refine the raw data and organize it into the final structure.

data_filtering.py: Uses Pandas to filter out garbage URLs, broken links, and irrelevant domains (for ex "login" pages or "privacy policy" pages).

data_filtering_forums.py: Specific filtering logic for forums URLs, ensuring links come from popular sites like Reddit or StackExchange rather than news articles or other irrelevant websites.

data_filtering_main_table.py: Loads a pre-defined list of clean company data into the database, bypassing the scraping process for specific entries. (main_table was created to be used as a test inside n8n)

### Phase 3: Data Enrichment

setup_login_linkedin.py: A one-time setup script. Manually logs into Linkedin and saves your session cookies (linkedin_state.json) so the automation bots can bypass authentication walls later.

structured_linkedin_collector.py: Searches DuckDuckGo for "{Company Name} linkedin" to find the specific LinkedIn profile URL for each company in the database.

scrape_linkedin_profiles.py: Navigates to company profiles, handles popups, mimics human behavior, and extracts key data (Company Size, HQ, Industry, Products, Specialties, etc).

### Phase 4: Forums - pros and cons

structured_forums_collector.py: Searches specific queries (search_terms = "Why is {company} bad?", "Opinions on {company}") to find authentic user reviews and complaints on Reddit, Quora, and other forums. We do not have a scraper script for forums here since we had decided to handle this case inside the n8n workflow.

### Phase 5: Consolidation

constructing_main_table.py: Merges the gathered URL data and the scraped Linkedin details into one master table (main_table). We did this in order to simplify the workflow inside n8n.


## Utilities and Maintenance

### Database Viewers

Use these scripts to debug or view the data collected at each stage without opening the SQLite file directly.

view_google_search_results.py: View the initial list of blogs found and the urls and a status in order to know if the blog has been scraped already or not.

view_companies_url.py: View the list of extracted company websites.

view_companies_linkedin.py: View the found Linkedin URLs.

view_companies_details.py: View the scraped Linkedin details (HQ, Size, etc.).

view_companies_discussions.py: View the collected forum discussion links.

view_main_table content.py: View the final merged dataset.

### Database Resetters

These scripts drop specific tables, allowing you to restart a specific part of the process without wiping the entire database.

drop_company_details.py: Clears scraped Linkedin details.

drop_companies_discussions.py: Clears forum data.

drop_companies_reddit.py: Clears Reddit-specific data(this script is no longer used).

## Requirements and Installation

### Prerequisites:

- Python version 3.x

- Playwright - used for browser automation

- Pandas - used for data cleaning

- Sqlite3 - used for embedded db

### Installation steps:

1) Create and Activate a Virtual Environment It is recommended to run this project in an isolated environment.

- Windows: python first run $\textbf{-m venv venv}$ and then run this $\textbf{.\venv\Scripts\activate}$

- MacOS or Linux: first run $\textbf{python3 -m venv venv}$ and then run $\textbf{source venv/bin/activate}$

2) Install Dependencies Once the virtual environment is active, install the required packages and browser binaries.

- first run: pip install -r requirements.txt

- after that run: playwright install

## Disclaimer

This tool is intended for educational purposes. Please respect the Terms of Service of the websites being scraped. The human_behaviour functions are implemented to reduce server load and mimic natural browsing.