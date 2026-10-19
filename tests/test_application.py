import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
sys.path.insert(0, str(APP))
import settings
from url_security import hostname_matches, is_linkedin_url


def load_script(path):
    spec = importlib.util.spec_from_file_location("tested_" + Path(path).stem.replace(" ", "_"), ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = str(Path(self.directory.name) / "research.db")

    def seed_database(self):
        with contextlib.closing(sqlite3.connect(self.database)) as connection, connection:
            connection.executescript("""
                CREATE TABLE companies_url (source_blog_url TEXT, company_name TEXT, company_url TEXT, status TEXT);
                INSERT INTO companies_url VALUES ('https://blog.example.com', 'Example LMS', 'https://example.com/product', 'new');
                INSERT INTO companies_url VALUES ('https://blog.example.com', 'Example duplicate', 'https://example.com/about', 'new');
                INSERT INTO companies_url VALUES ('https://blog.example.com', 'Login', 'https://unwanted.example.org', 'new');
                CREATE TABLE companies_details (company_name TEXT, linkedin_url TEXT, company_size TEXT, headquarters TEXT);
                INSERT INTO companies_details VALUES ('Example LMS', 'https://www.linkedin.com/company/example', '11-50 employees', 'Berlin');
                CREATE TABLE companies_discussions (id INTEGER PRIMARY KEY, discussion_url TEXT);
                INSERT INTO companies_discussions VALUES (1, 'https://www.reddit.com/r/lms/comments/123');
                INSERT INTO companies_discussions VALUES (2, 'https://news.example.net/article/story');
                INSERT INTO companies_discussions VALUES (3, 'https://reddit.com.attacker.invalid/topic');
            """)

    def test_database_cleaning_consolidation_repeat_run_and_viewers(self):
        self.seed_database()
        cleaning = load_script("app/data_filtering.py")
        forums = load_script("app/data_filtering_forums.py")
        consolidation = load_script("app/constructing_main_table.py")
        for module in [cleaning, forums, consolidation]:
            module.db = self.database
        import tldextract
        extractor = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)
        with patch.object(cleaning.tldextract, "extract", side_effect=extractor), contextlib.redirect_stdout(io.StringIO()):
            cleaning.clean_database()
            forums.filter_database()
            consolidation.combine_tables()
            consolidation.combine_tables()
        with contextlib.closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT company_name, company_url FROM companies_url").fetchall(), [("Example LMS", "https://example.com")])
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM companies_discussions").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT company_name, headquarters FROM main_table").fetchall(), [("Example LMS", "Berlin")])
        for script in ["view_companies_url.py", "view_companies_details.py", "view_companies_discussions.py", "view_main_table content.py"]:
            result = subprocess.run([sys.executable, "-B", str(ROOT / "run.py"), script], cwd=self.directory.name,
                                    env={**os.environ, "MARKET_RESEARCH_DB": self.database}, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("Error:", result.stdout)

    def test_failed_consolidation_preserves_existing_output(self):
        self.seed_database()
        module = load_script("app/constructing_main_table.py")
        module.db = self.database
        module.combine_tables()
        with contextlib.closing(sqlite3.connect(self.database)) as connection, connection:
            previous = connection.execute("SELECT * FROM main_table").fetchall()
            connection.execute("DROP TABLE companies_details")
        with self.assertRaises(sqlite3.OperationalError):
            module.combine_tables()
        with contextlib.closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT * FROM main_table").fetchall(), previous)

    def test_scheduled_job_uses_existing_pipeline_and_fixed_working_directory(self):
        module = load_script("app/scheduler.py")
        with patch.object(module.subprocess, "run") as execute, contextlib.redirect_stdout(io.StringIO()):
            module.job()
        execute.assert_called_once_with([sys.executable, "-u", str(APP / "main_script.py")], check=True, cwd=APP)

    def test_paths_do_not_depend_on_current_working_directory(self):
        with patch.dict(os.environ, {"TEST_CONFIG_PATH": "relative/state.json"}):
            self.assertEqual(settings.configured_path("TEST_CONFIG_PATH"), APP / "relative/state.json")
        with patch.dict(os.environ, {"TEST_CONFIG_PATH": self.database}):
            self.assertEqual(settings.configured_path("TEST_CONFIG_PATH"), Path(self.database))

    def test_credentials_require_configuration_and_owner_only_permissions(self):
        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": ""}):
            with self.assertRaisesRegex(ValueError, "Set GOOGLE_APPLICATION_CREDENTIALS"):
                settings.google_credentials_path()
        key = Path(self.directory.name) / "service-account.json"
        key.write_text("{}")
        key.chmod(0o644)
        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": str(key)}):
            self.assertEqual(settings.google_credentials_path(), str(key))
        if os.name == "posix":
            self.assertEqual(key.stat().st_mode & 0o777, 0o600)

    def test_login_state_is_written_privately_and_atomically(self):
        path = Path(self.directory.name) / "session.json"
        path.write_text("old")
        path.chmod(0o666)
        settings.save_private_json(path, {"cookies": [], "origins": []})
        self.assertEqual(json.loads(path.read_text()), {"cookies": [], "origins": []})
        if os.name == "posix":
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(list(path.parent.glob(".login-state-*")), [])

    def test_domain_checks_reject_spoofed_linkedin_and_forum_hosts(self):
        for url in ["https://linkedin.com.attacker.invalid/company/demo", "https://example.invalid/linkedin.com/company/demo", "https://linkedin.com@attacker.invalid/company/demo", "javascript:linkedin.com/company/demo", None]:
            self.assertFalse(is_linkedin_url(url, company_only=True), url)
        for url in ["https://www.linkedin.com/company/demo", "https://de.linkedin.com/school/demo"]:
            self.assertTrue(is_linkedin_url(url, company_only=True), url)
        self.assertFalse(is_linkedin_url("https://www.linkedin.com/in/demo", company_only=True))
        self.assertFalse(hostname_matches("https://attacker.invalid/reddit.com", ["reddit.com"]))
        self.assertTrue(hostname_matches("https://old.reddit.com/r/lms", ["reddit.com"]))

    def test_migration_authentication_fails_before_any_sheet_write(self):
        module = load_script("scripts/migrations/from_db_to_googlesheet.py")
        with patch.object(module, "google_credentials_path", side_effect=ValueError("missing configuration")):
            with patch.object(module.gspread, "authorize") as authorize, contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "missing configuration"):
                    module.db_to_sheets()
        authorize.assert_not_called()

    def test_all_migrations_use_configured_credentials_and_expected_worksheets(self):
        self.seed_database()
        with contextlib.closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("CREATE TABLE clean_main_table AS SELECT * FROM companies_url")
        names = ["from_db_to_googlesheet.py", "from_db_to_googlesheet_linkedin.py", "from_db_to_googlesheet_forums.py", "from_db_to_googlesheet_main_table.py"]
        for name in names:
            with self.subTest(script=name):
                module = load_script("scripts/migrations/" + name)
                module.db = self.database
                with contextlib.ExitStack() as stack:
                    stack.enter_context(patch.dict(os.environ, {"GOOGLE_SHEET_ID": "fixture-sheet"}))
                    stack.enter_context(patch.object(module, "google_credentials_path", return_value="configured-credentials.json"))
                    credentials = stack.enter_context(patch.object(module.ServiceAccountCredentials, "from_json_keyfile_name"))
                    authorize = stack.enter_context(patch.object(module.gspread, "authorize"))
                    write = stack.enter_context(patch.object(module, "set_with_dataframe"))
                    stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                    module.db_to_sheets()
                credentials.assert_called_once_with("configured-credentials.json", ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.readonly"])
                authorize.return_value.open_by_key.assert_called_once_with("fixture-sheet")
                worksheet = authorize.return_value.open_by_key.return_value.worksheet
                worksheet.assert_called_once_with(module.worksheet_name)
                worksheet.return_value.clear.assert_called_once_with()
                write.assert_called_once()
                self.assertGreater(len(write.call_args.args[1]), 0)


if __name__ == "__main__":
    unittest.main()
