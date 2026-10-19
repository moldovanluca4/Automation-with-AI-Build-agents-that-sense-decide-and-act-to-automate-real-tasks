import argparse
import os
from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"
SCRIPT_DIRS = (
    APP,
    ROOT / "scripts" / "viewers",
    ROOT / "scripts" / "maintenance",
    ROOT / "scripts" / "migrations",
)


def available_scripts():
    scripts = {}
    for directory in SCRIPT_DIRS:
        for path in sorted(directory.glob("*.py")):
            if path.name in {"settings.py", "url_security.py"}:
                continue
            if path.name in scripts:
                raise RuntimeError(f"Duplicate script name: {path.name}")
            scripts[path.name] = path
    return scripts


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a market research script")
    parser.add_argument("--list", action="store_true", help="list available scripts")
    parser.add_argument("script", nargs="?", help="original filename, with or without .py")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="arguments for the original script")
    options = parser.parse_args(argv)
    scripts = available_scripts()
    if options.list:
        for name, path in scripts.items():
            print(f"{name}: {path.relative_to(ROOT)}")
        return 0
    if not options.script:
        parser.error("choose a script or use --list")
    name = options.script if options.script.endswith(".py") else options.script + ".py"
    if name not in scripts:
        parser.error(f"unknown script: {options.script}; use --list")

    target = scripts[name]
    previous_cwd = Path.cwd()
    previous_argv = sys.argv[:]
    previous_path = sys.path[:]
    try:
        os.chdir(APP)
        sys.argv = [str(target), *options.args]
        sys.path.insert(0, str(APP))
        sys.path.insert(0, str(target.parent))
        runpy.run_path(str(target), run_name="__main__")
    finally:
        os.chdir(previous_cwd)
        sys.argv[:] = previous_argv
        sys.path[:] = previous_path
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
