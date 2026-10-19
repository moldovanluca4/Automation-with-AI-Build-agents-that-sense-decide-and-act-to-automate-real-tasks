import ast
import hashlib
import json
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest_path = ROOT / "docs/restructure-manifest.json"
    revisions_path = ROOT / "docs/security/security-changes.json"
    manifest = {"files": []}
    revisions = {}
    if manifest_path.is_file() and revisions_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        revisions = json.loads(revisions_path.read_text())["files"]
    changed = 0
    for item in manifest["files"]:
        path = ROOT / item["destination"]
        if not path.is_file():
            raise SystemExit(f"Missing preserved file: {item['destination']}")
        revision = revisions.get(item["destination"])
        if revision and revision["original_sha256"] != item["sha256"]:
            raise SystemExit(f"Invalid revision baseline: {item['destination']}")
        expected = revision["sha256"] if revision else item["sha256"]
        changed += bool(revision)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"Content changed: {item['destination']}")

    scripts = []
    for directory in ["app", "scripts", "tests", "tools"]:
        scripts.extend((ROOT / directory).rglob("*.py"))
    scripts.extend(ROOT.glob("*.py"))
    for path in scripts:
        ast.parse(path.read_text(), filename=str(path))

    pipeline = ast.parse((ROOT / "app/main_script.py").read_text())
    assignments = {
        node.targets[0].id: node.value for node in pipeline.body
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
    }
    steps = ast.literal_eval(assignments["pipeline_steps"])
    names = [step["script"] for step in steps]
    names.append(ast.literal_eval(assignments["login_helper"]))
    for name in names:
        if not (ROOT / "app" / name).is_file():
            raise SystemExit(f"Pipeline target missing: {name}")

    json.loads((ROOT / "workflows/n8n_hackathon.json").read_text())
    with (ROOT / "pyproject.toml").open("rb") as config_file:
        tomllib.load(config_file)
    print(f"Verified {len(manifest['files'])} baseline public files ({changed} approved revisions), "
          f"{len(scripts)} Python syntax checks, {len(names)} pipeline targets, workflow JSON, and TOML configuration.")
    print("Local ignored data and credentials are intentionally excluded from this public manifest.")


if __name__ == "__main__":
    main()
