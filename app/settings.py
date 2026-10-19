import json
import os
from pathlib import Path
import re
import tempfile
import tomllib

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv(APP_DIR / ".env")


def load_config(path=None):
    selected = path or os.environ.get("MARKET_RESEARCH_CONFIG")
    source = Path(selected).expanduser() if selected else ROOT_DIR / "pyproject.toml"
    if not source.is_absolute():
        source = ROOT_DIR / source
    if not source.is_file():
        if selected:
            raise ValueError(f"Configuration file not found: {source}")
        return {}
    try:
        with source.open("rb") as input_file:
            document = tomllib.load(input_file)
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"Invalid TOML configuration in {source}") from error
    tool = document.get("tool", {})
    if not isinstance(tool, dict):
        raise ValueError("TOML tool must be a table")
    config = tool.get("market-research", {})
    schema = {
        "paths": {"database": str, "linkedin_state": str},
        "google": {"sheet_name": str, "sheet_id": str},
        "scheduler": {"day": str, "time": str, "poll_interval_seconds": int},
    }
    if not isinstance(config, dict) or config.keys() - schema.keys():
        raise ValueError("Unknown or invalid market-research configuration section")
    for section, options in config.items():
        if not isinstance(options, dict) or options.keys() - schema[section].keys():
            raise ValueError(f"Unknown or invalid configuration option in {section}")
        for name, value in options.items():
            if type(value) is not schema[section][name]:
                raise ValueError(f"Invalid type for {section}.{name}")
            if not value and (section, name) != ("google", "sheet_id"):
                raise ValueError(f"Configuration value {section}.{name} cannot be empty")
    scheduler = config.get("scheduler", {})
    if scheduler.get("day", "monday") not in {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}:
        raise ValueError("scheduler.day must be a lowercase weekday name")
    if not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", scheduler.get("time", "09:00")):
        raise ValueError("scheduler.time must use 24-hour HH:MM format")
    if scheduler.get("poll_interval_seconds", 60) <= 0:
        raise ValueError("scheduler.poll_interval_seconds must be positive")
    return config


CONFIG = load_config()


def configured_path(variable, default=None):
    option = {"MARKET_RESEARCH_DB": "database", "LINKEDIN_STATE_PATH": "linkedin_state"}.get(variable)
    if option:
        default = CONFIG.get("paths", {}).get(option, default)
    value = os.environ.get(variable) or default
    if not value:
        raise ValueError(f"Set {variable} in the environment or .env before using this integration")
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (APP_DIR / path).resolve()


DATABASE_PATH = str(configured_path("MARKET_RESEARCH_DB", "companies_url.db"))
LINKEDIN_STATE_PATH = str(configured_path("LINKEDIN_STATE_PATH", "linkedin_state.json"))
SCHEDULE_DAY = CONFIG.get("scheduler", {}).get("day", "monday")
SCHEDULE_TIME = CONFIG.get("scheduler", {}).get("time", "09:00")
SCHEDULE_POLL_INTERVAL = CONFIG.get("scheduler", {}).get("poll_interval_seconds", 60)


def google_sheet_name():
    return os.environ.get("GOOGLE_SHEET_NAME") or CONFIG.get("google", {}).get("sheet_name", "Companies URL")


def google_sheet_id():
    return os.environ.get("GOOGLE_SHEET_ID") or CONFIG.get("google", {}).get("sheet_id") or None


def google_credentials_path():
    path = configured_path("GOOGLE_APPLICATION_CREDENTIALS")
    if not path.is_file():
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS must point to a local service-account JSON file")
    if os.name == "posix":
        path.chmod(0o600)
    return str(path)


def save_private_json(path, value):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=destination.parent, prefix=".login-state-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(value, output)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
