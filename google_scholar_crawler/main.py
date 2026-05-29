import json
from datetime import datetime
import os
import signal
from pathlib import Path

from scholarly import scholarly


SCHOLAR_ID = os.environ.get("GOOGLE_SCHOLAR_ID", "g9xvPCAAAAAJ").strip()
TIMEOUT_SECONDS = int(os.environ.get("SCHOLARLY_TIMEOUT_SECONDS", "240"))
RESULTS_DIR = Path(__file__).resolve().parent / "results"
DATA_PATH = RESULTS_DIR / "gs_data.json"
SHIELDS_PATH = RESULTS_DIR / "gs_data_shieldsio.json"


class ScholarFetchTimeout(TimeoutError):
    pass


def _timeout_handler(signum, frame):
    raise ScholarFetchTimeout(f"Google Scholar fetch timed out after {TIMEOUT_SECONDS} seconds")


def _load_existing_data():
    if not DATA_PATH.exists():
        return None
    with DATA_PATH.open(encoding="utf-8") as infile:
        return json.load(infile)


def _fetch_author_data():
    if not SCHOLAR_ID:
        raise RuntimeError("GOOGLE_SCHOLAR_ID is empty")

    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["basics", "indices", "counts", "publications"])
    author["updated"] = str(datetime.utcnow())
    author["publications"] = {
        publication["author_pub_id"]: publication
        for publication in author.get("publications", [])
        if publication.get("author_pub_id")
    }
    return author


def _write_results(author):
    RESULTS_DIR.mkdir(exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as outfile:
        json.dump(author, outfile, ensure_ascii=False)

    cited_by = author.get("citedby", 0)
    shieldio_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(cited_by),
    }
    with SHIELDS_PATH.open("w", encoding="utf-8") as outfile:
        json.dump(shieldio_data, outfile, ensure_ascii=False)


def main():
    existing_data = _load_existing_data()

    try:
        if hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(TIMEOUT_SECONDS)
        author = _fetch_author_data()
    except Exception as exc:
        if existing_data:
            author = existing_data
            author["citation_fetch_error"] = f"{type(exc).__name__}: {exc}"
            print(f"Warning: using previous citation data because fetch failed: {exc}")
        else:
            author = {
                "name": "Kaiqiang Lin",
                "citedby": 0,
                "publications": {},
                "updated": str(datetime.utcnow()),
                "citation_fetch_error": f"{type(exc).__name__}: {exc}",
            }
            print(f"Warning: writing placeholder citation data because fetch failed: {exc}")
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)

    print(json.dumps(author, indent=2, ensure_ascii=False))
    _write_results(author)


if __name__ == "__main__":
    main()
