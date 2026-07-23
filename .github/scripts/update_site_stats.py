#!/usr/bin/env python3
"""Publish monotonic homepage view and visitor counters."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


DEFAULT_API_URL = (
    "https://events.vercount.one/api/v2/log"
    "?url=https%3A%2F%2Flkq1220.github.io%2F"
)


def parse_counter(value: Any, name: str, *, allow_zero: bool) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")

    try:
        counter = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc

    minimum = 0 if allow_zero else 1
    if counter < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return counter


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def fetch_vercount(api_url: str, timeout: float) -> dict[str, Any]:
    request = Request(
        api_url,
        headers={"User-Agent": "lkq1220-site-stats/1.0"},
        method="GET",
    )
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Vercount returned HTTP {response.status}")
        payload = json.load(response)

    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise RuntimeError("Vercount returned an unsuccessful response")
    if not isinstance(payload.get("data"), dict):
        raise RuntimeError("Vercount response is missing counter data")
    return payload["data"]


def build_snapshot(
    previous: dict[str, Any],
    source: dict[str, Any],
    checked_at: str,
) -> dict[str, Any]:
    previous_views = parse_counter(previous.get("views"), "previous views", allow_zero=False)
    previous_visitors = parse_counter(
        previous.get("visitors"),
        "previous visitors",
        allow_zero=False,
    )
    source_views = parse_counter(source.get("page_pv"), "source page_pv", allow_zero=True)
    source_visitors = parse_counter(
        source.get("site_uv"),
        "source site_uv",
        allow_zero=True,
    )

    views = max(previous_views, source_views)
    visitors = max(previous_visitors, source_visitors)
    guarded = {
        "views": source_views < views,
        "visitors": source_visitors < visitors,
    }

    snapshot = {
        "schema_version": 1,
        "site": "lkq1220.github.io",
        "provider": "vercount",
        "views": views,
        "visitors": visitors,
        "source_views": source_views,
        "source_visitors": source_visitors,
        "source_metrics": {
            "views": "page_pv",
            "visitors": "site_uv",
        },
        "guarded": guarded,
        "updated_at": previous.get("updated_at", checked_at),
    }

    comparable_previous = dict(previous)
    comparable_previous.pop("updated_at", None)
    comparable_snapshot = dict(snapshot)
    comparable_snapshot.pop("updated_at", None)
    if comparable_snapshot != comparable_previous:
        snapshot["updated_at"] = checked_at

    return snapshot


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
    os.replace(temporary_path, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--timeout", default=15.0, type=float)
    args = parser.parse_args()

    previous = load_json(args.previous)
    source = fetch_vercount(args.api_url, args.timeout)
    checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )
    snapshot = build_snapshot(previous, source, checked_at)
    write_json_atomic(args.output, snapshot)

    print(
        "Published counters: "
        f"views={snapshot['views']} visitors={snapshot['visitors']} "
        f"guarded={snapshot['guarded']}"
    )


if __name__ == "__main__":
    main()
