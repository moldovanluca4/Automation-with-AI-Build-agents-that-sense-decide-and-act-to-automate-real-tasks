# Automation-with-AI-Build-agents-that-sense-decide-and-act-to-automate-real-tasks

## Award Winning Proj

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

## Project Structure

```text
app/                   Pipeline stages, collectors, filters, and shared settings
scripts/
  viewers/             Database inspection scripts
  maintenance/         Database reset scripts
  migrations/          Local Google Sheets exporters, excluded from Git
workflows/             n8n workflow export
docs/
  hackathon/           Project presentation and supporting documents
  references/          Notion webpage reference
tests/                 Application and configuration tests
tools/                 Structure verification
main_script.py         Entry point for the full pipeline
scheduler.py           Entry point for scheduled runs
run.py                 Launcher for individual scripts
pyproject.toml         Runtime configuration
requirements.txt       Pinned Python dependencies
.env.example           Environment variable template
```

The local SQLite database and saved LinkedIn session default to `app/companies_url.db` and `app/linkedin_state.json`. Credentials, runtime data, and local configuration are excluded from Git.

## Architecture and Workflow

The project is divided into distinct stages. `python main_script.py` runs discovery, company extraction, company filtering, LinkedIn enrichment, forum discovery, forum filtering, and consolidation in that order. The stage scripts live in `app/`.

### Phase 1: Discovery 

These scripts are responsible for finding and fetching initial data from the web.

structure_data_collector.py: Initiates the process by searching DuckDuckGo for competitor lists and storing the results.

gather_companies_url.py: Visits the blogs found in the previous step to extract specific company names and URLs. It filters out social media or garbage links to find the actual company homepages.

### Phase 2: Cleaning Data

These scripts refine the raw data and organize it into the final structure.

data_filtering.py: Uses Pandas to filter out garbage URLs, broken links, and irrelevant domains (for ex "login" pages or "privacy policy" pages).

### Phase 3: Data Enrichment

setup_login_linkedin.py: Logs into LinkedIn with your input and saves the session for later runs. Run it again when the saved session expires.

structured_linkedin_collector.py: An optional standalone collector that searches DuckDuckGo for "{Company Name} linkedin" and stores profile URLs. The full pipeline uses scrape_linkedin_profiles.py to search and enrich companies directly.

scrape_linkedin_profiles.py: Navigates to company profiles, handles popups, mimics human behavior, and extracts key data (Company Size, HQ, Industry, Products, Specialties, etc).

### Phase 4: Forums - pros and cons

structured_forums_collector.py: Searches specific queries (search_terms = "Why is {company} bad?", "Opinions on {company}") to find authentic user reviews and complaints on Reddit, Quora, and other forums. We do not have a scraper script for forums here since we had decided to handle this case inside the n8n workflow.

data_filtering_forums.py: Filters the collected discussion URLs to retain forum and review sources while removing irrelevant articles.

### Phase 5: Consolidation

constructing_main_table.py: Merges the gathered URL data and the scraped Linkedin details into one master table (main_table). We did this in order to simplify the workflow inside n8n.


## Data Migration & API Usage

To enable integration with n8n workflows, this project includes a set of custom migration scripts designed to transfer data from the local SQLite database to Google Sheets.
These scripts are available locally under `scripts/migrations/` when supplied separately and remain excluded from Git. They authenticate using a Google service-account JSON file configured through `GOOGLE_APPLICATION_CREDENTIALS`.

Excluded Scripts:

- from_db_to_googlesheet.py

- from_db_to_googlesheet_linkedin.py

- from_db_to_googlesheet_forums.py

- from_db_to_googlesheet_main_table.py

Place the service-account JSON in the ignored `app/credentials/` directory, set its path in `.env`, and grant that service account access to the destination spreadsheet. Configure the spreadsheet name or ID in `pyproject.toml` or through environment overrides.

Run an available exporter with `python run.py from_db_to_googlesheet` or the corresponding `_linkedin`, `_forums`, or `_main_table` name. Exporters clear the destination worksheet before writing; use the intended destination.

Import [workflows/n8n_hackathon.json](workflows/n8n_hackathon.json) into n8n and configure its Google Sheets, Gemini, and Notion credentials there. The Python pipeline does not automatically run the migration scripts or the n8n workflow.


## Utilities and Maintenance

### Database Viewers

Use the scripts in `scripts/viewers/` to debug or view the data collected at each stage without opening the SQLite file directly. Launch them from the project root with `python run.py <script_name>`.

view_google_search_result.py: View the initial list of blogs, their URLs, and processing status.

view_companies_url.py: View the list of extracted company websites.

view_companies_linkedin.py: View the found Linkedin URLs.

view_companies_details.py: View the scraped Linkedin details (HQ, Size, etc.).

view_companies_discussions.py: View the collected forum discussion links.

view_main_table content.py: View the final merged dataset.

### Database Resetters

The scripts in `scripts/maintenance/` drop specific tables, allowing you to restart a specific part of the process without wiping the entire database. Run them through `run.py` only when you intend to remove that table's data.

drop_company_details.py: Clears scraped Linkedin details.

drop_companies_discussions.py: Clears forum data.

## Requirements and Installation

### Prerequisites:

- Python 3.11 or newer, including the standard-library TOML parser

- Playwright - used for browser automation

- Pandas - used for data cleaning

- Sqlite3 - used for embedded db

- A graphical desktop for the browser collectors

### Installation steps:

1) Create and activate an isolated virtual environment.

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install the dependencies and browser binaries.

```bash
python -m pip install -r requirements.txt
python -m playwright install
```

## Configuration

Edit [pyproject.toml](pyproject.toml) to change the runtime defaults:

```toml
[tool.market-research.paths]
database = "companies_url.db"
linkedin_state = "linkedin_state.json"

[tool.market-research.google]
sheet_name = "Companies URL"
sheet_id = ""

[tool.market-research.scheduler]
day = "monday"
time = "09:00"
poll_interval_seconds = 60
```

Relative database, session, and credential paths resolve against `app/`; absolute paths are also supported. `sheet_id`, when provided, takes precedence over `sheet_name`. Scheduling uses the host's local timezone, a lowercase weekday, a 24-hour `HH:MM` time, and a positive integer polling interval in seconds.

Copy `.env.example` to `.env` for credentials or local overrides. For example:

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=credentials/google-service-account.json
```

This example points to `app/credentials/google-service-account.json`; supply your own service-account file. Keep key contents and login cookies out of TOML and version control. Google credentials are needed for exports, not for the discovery pipeline.

| Environment variable | Purpose |
| --- | --- |
| `MARKET_RESEARCH_CONFIG` | Use a different TOML configuration file |
| `MARKET_RESEARCH_DB` | Override the SQLite database path |
| `LINKEDIN_STATE_PATH` | Override the saved browser session path |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to the private service-account JSON |
| `GOOGLE_SHEET_ID` | Override the destination spreadsheet ID |
| `GOOGLE_SHEET_NAME` | Override the destination name when no ID is set |

Configuration precedence is: process environment, root `.env`, `app/.env`, then TOML defaults. Leave unused overrides empty to use the TOML values.

For a personal TOML file, copy `pyproject.toml` to the Git-ignored `config.local.toml` and set `MARKET_RESEARCH_CONFIG=config.local.toml` in `.env`. Relative configuration-file paths resolve against the repository root. Unknown settings, invalid types, or invalid schedule values cause an error at startup.

## Running the Project

With the environment activated, run these commands from the project root:

```bash
python main_script.py
```

To set up or refresh the LinkedIn session, list available scripts, or run a single stage or viewer:

```bash
python run.py setup_login_linkedin
python run.py --list
python run.py structure_data_collector
python run.py view_companies_url
python run.py "view_main_table content.py"
```

To keep the weekly scheduler running:

```bash
python scheduler.py
```

The default schedule is Monday at 09:00. Keep the scheduler process running for scheduled jobs to execute. The launchers resolve script locations independently of the current working directory.

## Disclaimer

This tool is intended for educational purposes. Please respect the Terms of Service of the websites being scraped. The human_behaviour functions are implemented to reduce server load and mimic natural browsing.
