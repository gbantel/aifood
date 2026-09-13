import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("launch", Path(__file__).with_name("headroom_codex.py"))
launch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch)


class LauncherTests(unittest.TestCase):
    def test_environment_preserves_codex_and_disables_persistence(self):
        before = os.environ.copy()
        env = launch.environment(Path("runtime"))
        self.assertEqual(os.environ, before)
        for key in ("CODEX_HOME", "OPENAI_API_KEY", "OPENAI_BASE_URL"):
            self.assertEqual(env.get(key), before.get(key))
        self.assertEqual(env["HEADROOM_STATELESS"], "true")
        self.assertEqual(env["HEADROOM_CCR_BACKEND"], "memory")
        self.assertEqual(env["HEADROOM_BEACON"], "off")

    def test_existing_configuration_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = root / "runtime"
            for exe in launch.executables(runtime):
                exe.parent.mkdir(parents=True, exist_ok=True)
                exe.touch()
            config = root / ".codex" / "config.toml"
            config.parent.mkdir()
            original = 'model = "preserve-me"\n'
            config.write_text(original, encoding="utf-8")
            with patch.object(launch, "ROOT", root), patch.object(
                launch.subprocess, "check_output", return_value=launch.VERSION
            ), self.assertRaises(SystemExit) as error:
                launch.main(["--runtime", str(runtime), "configure-mcp"])
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_codex_arguments_are_not_headroom_options(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp)
            for exe in launch.executables(runtime):
                exe.parent.mkdir(parents=True, exist_ok=True)
                exe.touch()
            with patch.object(launch.subprocess, "check_output", return_value=launch.VERSION), \
                 patch.object(launch.shutil, "which", return_value="codex"), \
                 patch.object(launch.subprocess, "call", return_value=7) as call:
                result = launch.main(["--runtime", str(runtime), "run", "--", "--learn", "two words"])
            self.assertEqual(result, 7)
            command = call.call_args.args[0]
            self.assertEqual(command[1:], ["wrap", "codex", "--code-memory", "none", "--", "--learn", "two words"])


if __name__ == "__main__":
    unittest.main()
