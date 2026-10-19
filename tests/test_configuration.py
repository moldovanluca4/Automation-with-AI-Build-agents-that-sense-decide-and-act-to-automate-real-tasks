import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_application import APP, ROOT, load_script
import settings


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "custom.toml"

    def test_checked_in_defaults_preserve_existing_behavior(self):
        config = settings.load_config(ROOT / "pyproject.toml")
        self.assertEqual(config["paths"], {"database": "companies_url.db", "linkedin_state": "linkedin_state.json"})
        self.assertEqual(config["google"], {"sheet_name": "Companies URL", "sheet_id": ""})
        self.assertEqual(config["scheduler"], {"day": "monday", "time": "09:00", "poll_interval_seconds": 60})

    def test_toml_values_and_nonempty_environment_overrides(self):
        self.path.write_text('[tool.market-research.paths]\ndatabase = "custom.db"\nlinkedin_state = "private/session.json"\n[tool.market-research.google]\nsheet_name = "Research"\nsheet_id = "fixture-sheet"\n')
        config = settings.load_config(self.path)
        with patch.object(settings, "CONFIG", config), patch.dict(os.environ, {
            "MARKET_RESEARCH_DB": "", "LINKEDIN_STATE_PATH": "", "GOOGLE_SHEET_NAME": "", "GOOGLE_SHEET_ID": "",
        }):
            self.assertEqual(settings.configured_path("MARKET_RESEARCH_DB"), APP / "custom.db")
            self.assertEqual(settings.configured_path("LINKEDIN_STATE_PATH"), APP / "private/session.json")
            self.assertEqual(settings.google_sheet_name(), "Research")
            self.assertEqual(settings.google_sheet_id(), "fixture-sheet")
            with patch.dict(os.environ, {"MARKET_RESEARCH_DB": "override.db", "GOOGLE_SHEET_NAME": "Override", "GOOGLE_SHEET_ID": "override-sheet"}):
                self.assertEqual(settings.configured_path("MARKET_RESEARCH_DB"), APP / "override.db")
                self.assertEqual(settings.google_sheet_name(), "Override")
                self.assertEqual(settings.google_sheet_id(), "override-sheet")

    def test_custom_configuration_loads_from_another_working_directory(self):
        self.path.write_text('[tool.market-research.paths]\ndatabase = "custom.db"\n[tool.market-research.scheduler]\nday = "friday"\ntime = "14:45"\npoll_interval_seconds = 10\n')
        program = 'import sys,json;sys.path.insert(0,sys.argv[1]);import settings;print(json.dumps([settings.DATABASE_PATH,settings.SCHEDULE_DAY,settings.SCHEDULE_TIME,settings.SCHEDULE_POLL_INTERVAL]))'
        result = subprocess.run([sys.executable, "-B", "-c", program, str(APP)], cwd=self.directory.name,
                                env={**os.environ, "MARKET_RESEARCH_CONFIG": str(self.path), "MARKET_RESEARCH_DB": ""},
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [str(APP / "custom.db"), "friday", "14:45", 10])

    def test_invalid_options_types_and_schedule_values_fail_clearly(self):
        examples = [
            '[tool.market-research.paths]\ndatabse = "typo.db"',
            '[tool.market-research.paths]\ndatabase = 12',
            '[tool.market-research.paths]\ndatabase = ""',
            '[tool.market-research.scheduler]\nday = "not-a-day"',
            '[tool.market-research.scheduler]\ntime = "25:00"',
            '[tool.market-research.scheduler]\npoll_interval_seconds = 0',
            '[tool.market-research.scheduler]\npoll_interval_seconds = true',
        ]
        for value in examples:
            with self.subTest(value=value):
                self.path.write_text(value)
                with self.assertRaises(ValueError):
                    settings.load_config(self.path)

    def test_missing_or_malformed_selected_file_fails_clearly(self):
        with self.assertRaisesRegex(ValueError, "Configuration file not found"):
            settings.load_config(self.path)
        self.path.write_text("[broken")
        with self.assertRaisesRegex(ValueError, "Invalid TOML configuration"):
            settings.load_config(self.path)

    def test_credentials_are_not_accepted_in_public_toml_configuration(self):
        self.path.write_text('[tool.market-research.google]\ncredentials = "not-a-secret"\n')
        with self.assertRaisesRegex(ValueError, "Unknown or invalid configuration option"):
            settings.load_config(self.path)

    def test_scheduler_registers_configured_day_time_and_poll_interval(self):
        module = load_script("app/scheduler.py")
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(module, "SCHEDULE_DAY", "friday"))
            stack.enter_context(patch.object(module, "SCHEDULE_TIME", "14:45"))
            stack.enter_context(patch.object(module, "SCHEDULE_POLL_INTERVAL", 10))
            every = stack.enter_context(patch.object(module.schedule, "every"))
            stack.enter_context(patch.object(module.schedule, "run_pending"))
            sleep = stack.enter_context(patch.object(module.time, "sleep", side_effect=SystemExit(0)))
            with self.assertRaises(SystemExit):
                module.main()
        every.return_value.friday.at.assert_called_once_with("14:45")
        every.return_value.friday.at.return_value.do.assert_called_once_with(module.job)
        sleep.assert_called_once_with(10)


if __name__ == "__main__":
    unittest.main()
