import importlib.util
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "skills" / "local-memory" / "scripts" / "memctl.py"
SPEC = importlib.util.spec_from_file_location("memctl", SCRIPT)
memctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(memctl)


class MemoryControllerTest(unittest.TestCase):
    def test_save_search_show_and_reindex(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body_file = root / "summary.md"
            body_file.write_text("# Task\n\nA reusable decision about retry behavior.\n", encoding="utf-8")
            save_args = Namespace(
                root=str(root), title="Retry behavior", source="test-agent", tags="retry,http",
                summary="Recorded the retry decision", outcome="decision", file=str(body_file),
            )
            with redirect_stdout(StringIO()):
                memctl.save(save_args)

            conversations, database = memctl.memory_paths(root)
            self.assertEqual(1, len(list(conversations.glob("*.md"))))
            self.assertTrue(database.exists())

            search_output = StringIO()
            with redirect_stdout(search_output):
                memctl.search(Namespace(root=str(root), query="retry", limit=10))
            self.assertIn("Retry behavior", search_output.getvalue())

            show_output = StringIO()
            with redirect_stdout(show_output):
                memctl.show(Namespace(root=str(root), id=1))
            self.assertIn("A reusable decision", show_output.getvalue())

            database.unlink()
            with redirect_stdout(StringIO()):
                memctl.reindex(Namespace(root=str(root)))
            rebuilt_output = StringIO()
            with redirect_stdout(rebuilt_output):
                memctl.search(Namespace(root=str(root), query="retry", limit=10))
            self.assertIn("Retry behavior", rebuilt_output.getvalue())

    def test_slugify_has_safe_fallback(self):
        self.assertEqual("conversation", memctl.slugify("***"))
        self.assertEqual("retry-settings", memctl.slugify("Retry settings"))


if __name__ == "__main__":
    unittest.main()
