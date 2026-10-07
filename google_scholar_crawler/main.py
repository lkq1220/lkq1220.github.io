import argparse
import json
from datetime import datetime, timezone
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup


SCHOLAR_ID = os.environ.get("GOOGLE_SCHOLAR_ID", "g9xvPCAAAAAJ").strip()
PROFILE_URL = "https://scholar.google.com/citations"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


def _load_existing_data(results_dir):
    data_path = results_dir / "gs_data.json"
    if not data_path.exists():
        return None
    with data_path.open(encoding="utf-8") as infile:
        return json.load(infile)


def _counter(text):
    text = text.replace(",", "").replace("\u00a0", "").strip().rstrip("*")
    if not text.isascii() or not text.isdigit():
        raise ValueError(f"Invalid Google Scholar counter: {text!r}")
    return int(text)


def _parse_profile(html):
    soup = BeautifulSoup(html, "html.parser")
    name = soup.select_one("#gsc_prf_in")
    metrics = soup.select("#gsc_rsb_st .gsc_rsb_std")
    if name is None or not metrics:
        raise RuntimeError("Google Scholar returned no citation table (blocked or changed page)")

    author = {"scholar_id": SCHOLAR_ID, "name": name.get_text(strip=True)}
    metric_names = ("citedby", "citedby5y", "hindex", "hindex5y", "i10index", "i10index5y")
    for metric, cell in zip(metric_names, metrics):
        author[metric] = _counter(cell.get_text())

    publications = {}
    for row in soup.select(".gsc_a_tr"):
        title = row.select_one(".gsc_a_at[href]")
        count = row.select_one(".gsc_a_ac")
        if title is None or count is None:
            raise RuntimeError("Google Scholar returned an incomplete publication row")
        paper_id = parse_qs(urlparse(title["href"]).query).get("citation_for_view", [""])[0]
        if not paper_id.startswith(SCHOLAR_ID + ":") or paper_id in publications:
            raise RuntimeError("Google Scholar returned an invalid or duplicate publication ID")
        details = row.select(".gsc_a_t .gs_gray")
        year = row.select_one(".gsc_a_y")
        publications[paper_id] = {
            "author_pub_id": paper_id,
            "bib": {
                "title": title.get_text(" ", strip=True),
                "author": details[0].get_text(" ", strip=True) if details else "",
                "citation": details[1].get_text(" ", strip=True) if len(details) > 1 else "",
                "pub_year": year.get_text(strip=True) if year else "",
            },
            "num_citations": _counter(count.get_text()) if count.get_text(strip=True) else 0,
        }

    if author["citedby"] > 0 and not publications:
        raise RuntimeError("Google Scholar returned a citation total without publications")
    author["publications"] = publications
    more = soup.select_one("#gsc_bpf_more")
    has_more = not more.has_attr("disabled") if more is not None else len(publications) == 100
    return author, has_more


def _fetch_author_data():
    if not SCHOLAR_ID:
        raise RuntimeError("GOOGLE_SCHOLAR_ID is empty")

    author = None
    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
        for start in range(0, 1000, 100):
            response = session.get(
                PROFILE_URL,
                params={"user": SCHOLAR_ID, "hl": "en", "pagesize": 100, "cstart": start},
                timeout=(10, 30),
            )
            if response.status_code != 200:
                raise RuntimeError(f"Google Scholar returned HTTP {response.status_code}; not publishing stale data")
            page, has_more = _parse_profile(response.text)
            if author is None:
                author = page
            else:
                if author["publications"].keys() & page["publications"].keys():
                    raise RuntimeError("Google Scholar pagination repeated a page")
                author["publications"].update(page["publications"])
            if not has_more:
                break
            if len(page["publications"]) != 100:
                raise RuntimeError("Google Scholar publication list was truncated")
        else:
            raise RuntimeError("Google Scholar pagination did not finish")

    author["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return author


def _write_results(author, results_dir):
    results_dir.mkdir(parents=True, exist_ok=True)
    data_path = results_dir / "gs_data.json"
    shields_path = results_dir / "gs_data_shieldsio.json"
    data_path.write_text(json.dumps(author, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shields_path.write_text(json.dumps({
        "schemaVersion": 1, "label": "citations", "message": str(author["citedby"]),
    }) + "\n", encoding="utf-8")


def main(results_dir=RESULTS_DIR):
    existing_data = _load_existing_data(results_dir)
    try:
        author = _fetch_author_data()
    except Exception as exc:
        if existing_data:
            # Keep the last successful timestamp and count, but mark this run as failed.
            existing_data["citation_fetch_error"] = f"{type(exc).__name__}: {exc}"
            _write_results(existing_data, results_dir)
        print(f"::error::Citation data was not refreshed: {type(exc).__name__}: {exc}")
        return 1

    _write_results(author, results_dir)
    print(f"Fetched {author['citedby']} citations across {len(author['publications'])} publications; updated {author['updated']} UTC")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    raise SystemExit(main(args.output_dir))
