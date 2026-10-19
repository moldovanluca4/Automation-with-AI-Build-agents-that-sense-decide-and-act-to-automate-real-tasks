import contextlib
import importlib.util
import io
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
spec = importlib.util.spec_from_file_location("project_launcher", ROOT / "run.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def test_launch_from_another_directory_preserves_arguments_and_context(self):
        original_cwd, original_argv, original_path = Path.cwd(), sys.argv[:], sys.path[:]
        target = ROOT / "scripts/viewers/view_companies_url.py"
        observed = {}

        def fake_run(path, run_name):
            observed.update(path=path, run_name=run_name, cwd=Path.cwd(), argv=sys.argv[:])

        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                with patch.object(launcher.runpy, "run_path", side_effect=fake_run):
                    self.assertEqual(launcher.main(["view_companies_url", "sample-argument"]), 0)
                self.assertEqual(Path.cwd(), Path(directory))
            finally:
                os.chdir(original_cwd)
        self.assertEqual(observed, {
            "path": str(target), "run_name": "__main__", "cwd": ROOT / "app",
            "argv": [str(target), "sample-argument"],
        })
        self.assertEqual(sys.argv, original_argv)
        self.assertEqual(sys.path, original_path)

    def test_script_failure_restores_context_and_propagates_exit_code(self):
        before = Path.cwd(), sys.argv[:], sys.path[:]
        with patch.object(launcher.runpy, "run_path", side_effect=SystemExit(7)):
            with self.assertRaises(SystemExit) as error:
                launcher.main(["main_script.py"])
        self.assertEqual(error.exception.code, 7)
        self.assertEqual((Path.cwd(), sys.argv, sys.path), before)

    def test_unknown_paths_cannot_escape_script_registry(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                launcher.main(["../../arbitrary.py"])
        self.assertEqual(error.exception.code, 2)

    def test_compatibility_entry_points_delegate_without_executing_pipeline(self):
        for name in ["main_script.py", "scheduler.py"]:
            with self.subTest(name=name), patch.dict(sys.modules, {"run": launcher}):
                with patch.object(launcher, "main", return_value=0) as main:
                    with patch.object(sys, "argv", [name, "argument"]):
                        with self.assertRaises(SystemExit) as error:
                            runpy.run_path(str(ROOT / name), run_name="__main__")
                self.assertEqual(error.exception.code, 0)
                main.assert_called_once_with([name, "argument"])

    def test_original_pipeline_keeps_subprocess_order_and_interpreter(self):
        pipeline = runpy.run_path(str(ROOT / "app/main_script.py"), run_name="audit_only")
        with patch("subprocess.run") as execute, patch("time.sleep"), patch("os.path.exists", return_value=True):
            with contextlib.redirect_stdout(io.StringIO()):
                pipeline["main"]()
        self.assertEqual(execute.call_args_list, [
            unittest.mock.call([sys.executable, "-u", str(ROOT / "app" / step["script"])], check=True, cwd=ROOT / "app")
            for step in pipeline["pipeline_steps"]
        ])


if __name__ == "__main__":
    unittest.main()
