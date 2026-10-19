import contextlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright
import tldextract

from test_application import load_script


def fixture_response(route):
    parsed = urlsplit(route.request.url)
    if parsed.hostname == "duckduckgo.com":
        query = parse_qs(parsed.query).get("q", [""])[0]
        if not query:
            html = '<form action="/" method="get"><input name="q"></form>'
        elif "linkedin" in query.lower():
            html = '<article><h2><a href="https://attacker.invalid/linkedin.com/company/fake">Fake</a></h2></article><article><h2><a href="https://www.linkedin.com/company/fixture-lms">Fixture LMS</a></h2></article>'
        elif query == "top LMS EdTech competitors list":
            html = '<li data-layout="organic"><h2><a href="https://research.example.org/lms">Research</a></h2></li>'
        else:
            html = '<article><h2><a href="https://www.reddit.com/r/lms/comments/123">LMS review</a></h2></article><article><h2><a href="https://www.trustpilot.com/review/fixturelms.com">LMS opinions</a></h2></article>'
    elif parsed.hostname == "research.example.org":
        html = '<a href="https://fixturelms.com">Fixture LMS</a><a href="https://facebook.com">Social</a>'
    elif parsed.hostname == "www.linkedin.com":
        html = '''<title>Fixture LMS | LinkedIn</title>
            <section class="artdeco-card"><p class="break-words">Fixture learning software</p></section>
            <div class="org-top-card-summary-info-list__info-item">E-Learning</div>
            <div class="org-top-card-summary-info-list__info-item">11-50 employees</div>
            <div class="org-top-card-summary-info-list__info-item">Berlin, Germany</div>
            <dl><dt>Headquarters</dt><dd>Berlin, Germany</dd><dt>Founded</dt><dd>2020</dd>
            <dt>Company size</dt><dd>11-50 employees</dd><dt>Website</dt><dd>https://fixturelms.com</dd></dl>'''
    else:
        route.abort()
        return
    route.fulfill(status=200, content_type="text/html", body=html)


class FixtureBrowser:
    def __init__(self, browser):
        self.browser = browser

    def new_context(self, **kwargs):
        context = self.browser.new_context(**kwargs)
        context.route("**/*", fixture_response)
        return context

    def new_page(self):
        return self.new_context().new_page()

    def close(self):
        self.browser.close()


class FixtureBrowserType:
    def __init__(self, browser_type):
        self.browser_type = browser_type

    def launch(self, **kwargs):
        kwargs.update(headless=True, slow_mo=0)
        return FixtureBrowser(self.browser_type.launch(**kwargs))


class FixturePlaywright:
    def __enter__(self):
        self.manager = sync_playwright()
        playwright = self.manager.__enter__()
        return SimpleNamespace(firefox=FixtureBrowserType(playwright.firefox), chromium=FixtureBrowserType(playwright.chromium))

    def __exit__(self, *args):
        return self.manager.__exit__(*args)


class BrowserPipelineSmokeTest(unittest.TestCase):
    def test_real_browsers_complete_all_pipeline_stages_using_local_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "fixture.db")
            session = Path(directory) / "fixture-session.json"
            session.write_text(json.dumps({"cookies": [], "origins": []}))
            stages = [
                ("app/structure_data_collector.py", "scrape_and_save"),
                ("app/gather_companies_url.py", "extract_companies"),
                ("app/data_filtering.py", "clean_database"),
                ("app/scrape_linkedin_profiles.py", "main_scraper"),
                ("app/structured_forums_collector.py", "scrape_forums"),
                ("app/data_filtering_forums.py", "filter_database"),
                ("app/constructing_main_table.py", "combine_tables"),
            ]
            extractor = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)
            for script, function in stages:
                with self.subTest(stage=script):
                    module = load_script(script)
                    module.db = database
                    if hasattr(module, "cookie_file"):
                        module.cookie_file = str(session)
                    output = io.StringIO()
                    with contextlib.ExitStack() as stack:
                        stack.enter_context(contextlib.redirect_stdout(output))
                        stack.enter_context(patch("time.sleep"))
                        stack.enter_context(patch.object(tldextract, "extract", side_effect=extractor))
                        if hasattr(module, "sync_playwright"):
                            stack.enter_context(patch.object(module, "sync_playwright", FixturePlaywright))
                        getattr(module, function)()
                    self.assertNotIn("error", output.getvalue().lower(), output.getvalue())
            with contextlib.closing(sqlite3.connect(database)) as connection:
                self.assertEqual(connection.execute("SELECT company_name, company_url FROM companies_url").fetchall(), [("Fixture LMS", "https://fixturelms.com")])
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM companies_discussions").fetchone()[0], 2)
                self.assertEqual(connection.execute("SELECT company_name, headquarters, company_size FROM main_table").fetchall(), [("Fixture LMS", "Berlin, Germany", "11-50 employees")])


if __name__ == "__main__":
    unittest.main()
