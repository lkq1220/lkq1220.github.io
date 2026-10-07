import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

import main as crawler


def profile(count="495", papers=1, start=0, more=False):
    rows = "".join(
        f'<tr class="gsc_a_tr"><td class="gsc_a_t">'
        f'<a class="gsc_a_at" href="/citations?citation_for_view={crawler.SCHOLAR_ID}:paper{i}">'
        f'Wireless &amp; underground research {i}</a>'
        f'<div class="gs_gray">K Lin</div><div class="gs_gray">IEEE, 2026</div></td>'
        f'<td><a class="gsc_a_ac">{"100" if i == 0 else ""}</a></td>'
        f'<td class="gsc_a_y">2026</td></tr>'
        for i in range(start, start + papers)
    )
    disabled = "" if more else "disabled"
    # No canonical link or author email: neither is needed for citation statistics.
    return (f'<div id="gsc_prf_in">Kaiqiang Lin</div>'
            f'<table id="gsc_rsb_st"><td class="gsc_rsb_std">{count}</td></table>'
            f'{rows}<button id="gsc_bpf_more" {disabled}>Show more</button>')


def response(html=None, status=200):
    return Mock(status_code=status, text=html if html is not None else profile())


class CitationCrawlerTests(unittest.TestCase):
    def fetch(self, responses):
        session = Mock()
        session.get.side_effect = responses
        with patch.object(crawler.requests, "Session") as factory:
            factory.return_value.__enter__.return_value = session
            data = crawler._fetch_author_data()
        return data, session

    def test_parse_without_fragile_author_metadata(self):
        data, more = crawler._parse_profile(profile())
        self.assertEqual(data["citedby"], 495)
        paper = data["publications"][crawler.SCHOLAR_ID + ":paper0"]
        self.assertEqual(paper["num_citations"], 100)
        self.assertEqual(paper["bib"]["title"], "Wireless & underground research 0")
        self.assertFalse(more)

    def test_zero_citations_and_empty_paper_counter(self):
        data, _ = crawler._parse_profile(profile(count="0", start=1))
        self.assertEqual(data["citedby"], 0)
        self.assertEqual(data["publications"][crawler.SCHOLAR_ID + ":paper1"]["num_citations"], 0)

    def test_counters_and_invalid_values(self):
        self.assertEqual(crawler._counter("1,234*"), 1234)
        for text in ("-1", "unknown", ""):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    crawler._counter(text)

    def test_blocked_or_incomplete_page_is_rejected(self):
        for html in ("<title>Captcha</title>", profile(papers=0),
                     profile().replace("citation_for_view=", "missing_id="),
                     profile().replace('class="gsc_a_ac"', 'class="missing"')):
            with self.subTest(html=html[:80]):
                with self.assertRaises(RuntimeError):
                    crawler._parse_profile(html)

    def test_one_request_fetches_complete_profile(self):
        data, session = self.fetch([response()])
        self.assertEqual(data["citedby"], 495)
        self.assertIn("updated", data)
        session.get.assert_called_once()
        self.assertEqual(session.get.call_args.kwargs["timeout"], (10, 30))
        self.assertEqual(session.get.call_args.kwargs["params"]["pagesize"], 100)

    def test_paginated_publications(self):
        data, session = self.fetch([
            response(profile(papers=100, more=True)),
            response(profile(papers=1, start=100)),
        ])
        self.assertEqual(len(data["publications"]), 101)
        self.assertEqual(session.get.call_args.kwargs["params"]["cstart"], 100)

    def test_incomplete_or_repeated_pagination_is_rejected(self):
        for pages in ([response(profile(more=True))],
                      [response(profile(papers=100, more=True))] * 2):
            with self.subTest(pages=len(pages)):
                with self.assertRaises(RuntimeError):
                    self.fetch(pages)

    def test_http_blocks_fail_without_long_retries(self):
        for code in (403, 429, 503):
            with self.subTest(code=code):
                with self.assertRaisesRegex(RuntimeError, f"HTTP {code}"):
                    self.fetch([response(status=code)])

    def test_timeout_propagates(self):
        with self.assertRaises(requests.Timeout):
            self.fetch([requests.Timeout("timed out")])

    def test_failed_fetch_retains_old_data_and_returns_failure(self):
        old = {"citedby": 474, "updated": "2026-09-06 12:04:57", "publications": {}}
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory)
            crawler._write_results(old, results)
            with patch.object(crawler, "_fetch_author_data", side_effect=requests.Timeout("timed out")), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                status = crawler.main(results)
            saved = json.loads((results / "gs_data.json").read_text())
        self.assertEqual(status, 1)
        self.assertEqual(saved["citedby"], 474)
        self.assertEqual(saved["updated"], old["updated"])
        self.assertIn("Timeout", saved["citation_fetch_error"])
        self.assertIn("::error::", output.getvalue())

    def test_failed_initial_fetch_does_not_invent_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory)
            with patch.object(crawler, "_fetch_author_data", side_effect=RuntimeError("HTTP 429")), \
                    contextlib.redirect_stdout(io.StringIO()):
                status = crawler.main(results)
            self.assertEqual(status, 1)
            self.assertFalse((results / "gs_data.json").exists())

    def test_success_replaces_old_error_and_keeps_badge_consistent(self):
        fresh, _ = crawler._parse_profile(profile())
        fresh["updated"] = "2026-10-07 18:00:00"
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory)
            crawler._write_results({"citedby": 474, "citation_fetch_error": "old error"}, results)
            with patch.object(crawler, "_fetch_author_data", return_value=fresh), \
                    contextlib.redirect_stdout(io.StringIO()):
                status = crawler.main(results)
            data = json.loads((results / "gs_data.json").read_text())
            badge = json.loads((results / "gs_data_shieldsio.json").read_text())
        self.assertEqual(status, 0)
        self.assertEqual(data["citedby"], 495)
        self.assertNotIn("citation_fetch_error", data)
        self.assertEqual(str(data["citedby"]), badge["message"])


if __name__ == "__main__":
    unittest.main()
