"""Fetch an existing fal.ai request result by request ID and download returned media."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from fal_generate import download_urls, find_urls


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    parser = argparse.ArgumentParser(description="Fetch a fal.ai result by request ID.")
    parser.add_argument("--model", required=True, help="fal endpoint id")
    parser.add_argument("--request-id", required=True, help="fal request ID")
    parser.add_argument("--out", default="Docs/MediaGeneration/outputs", help="Output folder")
    parser.add_argument("--no-download", action="store_true", help="Only save the JSON response.")
    parsed = parser.parse_args()

    if not os.environ.get("FAL_KEY"):
        print("FAL_KEY is not set.", file=sys.stderr)
        return 2

    try:
        import fal_client
    except ImportError:
        print("Missing dependency: fal-client.", file=sys.stderr)
        return 2

    out_dir = Path(parsed.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    status = fal_client.status(parsed.model, parsed.request_id, with_logs=True)
    print(f"Status: {status}")

    try:
        result = fal_client.result(parsed.model, parsed.request_id)
    except Exception as exc:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        error_path = out_dir / f"fal_fetch_error_{timestamp}_{parsed.request_id}.json"
        error_payload = {
            "model": parsed.model,
            "request_id": parsed.request_id,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        error_path.write_text(json.dumps(error_payload, indent=2), encoding="utf-8")
        print(f"Saved error JSON: {error_path}", file=sys.stderr)
        raise

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    result_path = out_dir / f"fal_result_{timestamp}_{parsed.request_id}.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved result JSON: {result_path}")

    if not parsed.no_download:
        urls = find_urls(result)
        media_paths = download_urls(urls, out_dir)
        for path in media_paths:
            print(f"Downloaded: {path}")
        if not media_paths:
            print("No downloadable URLs found in the fal response.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
