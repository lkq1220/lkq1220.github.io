import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import main as crawler


class CitationCrawlerTests(unittest.TestCase):
    def run_main(self, previous, fetch=None):
        output = io.StringIO()
        with patch.object(crawler, "_load_existing_data", return_value=previous), \
                patch.object(crawler, "_write_results") as write, \
                patch.object(crawler.signal, "alarm", create=True), \
                patch.object(crawler.signal, "signal"), \
                contextlib.redirect_stdout(output):
            if fetch is None:
                # Reproduce a dependency import failure inside the actual fetch.
                with patch.dict("sys.modules", {"scholarly": None}):
                    crawler.main()
            else:
                with patch.object(crawler, "_fetch_author_data", return_value=fetch):
                    crawler.main()
        return write.call_args.args[0], output.getvalue()

    def test_dependency_failure_preserves_count_and_successful_timestamp(self):
        previous = {"citedby": 474, "updated": "2026-09-06 12:04:57", "publications": {}}
        result, output = self.run_main(previous)
        self.assertEqual(result["citedby"], 474)
        self.assertEqual(result["updated"], "2026-09-06 12:04:57")
        self.assertIn("ModuleNotFoundError", result["citation_fetch_error"])
        self.assertIn("::warning::Citation data was not refreshed", output)

    def test_dependency_failure_without_previous_data_fails(self):
        with self.assertRaisesRegex(RuntimeError, "no previous citation data"):
            self.run_main(None)

    def test_success_replaces_stale_snapshot(self):
        previous = {"citedby": 474, "citation_fetch_error": "old error"}
        fresh = {"citedby": 500, "updated": "2026-10-07 12:00:00", "publications": {}}
        result, output = self.run_main(previous, fresh)
        self.assertEqual(result["citedby"], 500)
        self.assertNotIn("citation_fetch_error", result)
        self.assertNotIn("::warning::", output)

    def test_fetch_normalizes_publications_for_the_frontend(self):
        scholarly = Mock()
        scholarly.fill.return_value = {
            "citedby": 500,
            "publications": [
                {"author_pub_id": "g9xvPCAAAAAJ:paper", "num_citations": 12},
                {"bib": {"title": "No ID"}},
            ],
        }
        with patch.dict("sys.modules", {"scholarly": Mock(scholarly=scholarly)}):
            result = crawler._fetch_author_data()
        self.assertEqual(result["publications"]["g9xvPCAAAAAJ:paper"]["num_citations"], 12)
        self.assertEqual(len(result["publications"]), 1)
        self.assertIn("updated", result)

    def test_invalid_total_is_not_published_as_zero(self):
        scholarly = Mock()
        for count in (None, -1, True, "not a number"):
            with self.subTest(count=count):
                scholarly.fill.return_value = {"citedby": count}
                with patch.dict("sys.modules", {"scholarly": Mock(scholarly=scholarly)}):
                    with self.assertRaisesRegex(RuntimeError, "valid citation total"):
                        crawler._fetch_author_data()

    def test_json_and_badge_agree(self):
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory)
            with patch.object(crawler, "RESULTS_DIR", results), \
                    patch.object(crawler, "DATA_PATH", results / "gs_data.json"), \
                    patch.object(crawler, "SHIELDS_PATH", results / "gs_data_shieldsio.json"):
                crawler._write_results({"citedby": 500, "publications": {}})
            data = json.loads((results / "gs_data.json").read_text())
            badge = json.loads((results / "gs_data_shieldsio.json").read_text())
        self.assertEqual(str(data["citedby"]), badge["message"])

    def test_installed_dependencies_import(self):
        # Fails with bibtexparser 2.x, as the scheduled job did before the fix.
        self.assertIsNotNone(importlib.import_module("scholarly").scholarly)


if __name__ == "__main__":
    unittest.main()
