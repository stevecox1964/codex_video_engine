"""Run a fal.ai model from a JSON argument file and download returned media.

Example valid inputs:
  python Python/scripts/media/fal_generate.py --model fal-ai/flux/schnell --args Docs/MediaGeneration/recipes/text_to_image/brandbook_image.json --out Docs/MediaGeneration/outputs/text_to_image --project my_project
  python Python/scripts/media/fal_generate.py --model fal-ai/flux/dev --set prompt="a cinematic robot workshop" --set image_size=landscape_16_9
  python Python/scripts/media/fal_generate.py --model fal-ai/kling-video/v3/standard/image-to-video --args Docs/MediaGeneration/recipes/image_to_video/scene_001.json --upload-file start_image_url=Docs/MediaGeneration/outputs/text_to_image/scene_001.jpg
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def parse_scalar(value: str) -> Any:
    """Parse CLI values as JSON when possible, otherwise keep a string."""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def load_arguments(args_path: str | None, overrides: list[str]) -> dict[str, Any]:
    arguments: dict[str, Any] = {}
    if args_path:
        with open(args_path, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ValueError("The --args file must contain a JSON object.")
        arguments.update(loaded)

    for item in overrides:
        if "=" not in item:
            raise ValueError(f"--set value must be key=value, got: {item}")
        key, value = item.split("=", 1)
        arguments[key] = parse_scalar(value)

    return arguments


def apply_file_uploads(arguments: dict[str, Any], uploads: list[str]) -> None:
    """Upload local files to fal storage and assign their URLs to argument keys."""
    if not uploads:
        return

    import fal_client

    for item in uploads:
        if "=" not in item:
            raise ValueError(f"--upload-file value must be key=path, got: {item}")
        key, file_path = item.split("=", 1)
        path = Path(file_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            raise FileNotFoundError(f"Upload file does not exist: {path}")
        arguments[key] = fal_client.upload_file(str(path))


def find_urls(value: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        urls.append(value)
    elif isinstance(value, dict):
        for nested in value.values():
            urls.extend(find_urls(nested))
    elif isinstance(value, list):
        for nested in value:
            urls.extend(find_urls(nested))
    return urls


def safe_suffix(url: str, fallback: str) -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix
    if re.fullmatch(r"\.[A-Za-z0-9]{1,8}", suffix or ""):
        return suffix
    return fallback


def safe_project_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    cleaned = cleaned.strip("._-")
    if not cleaned:
        raise ValueError("--project must contain at least one letter or number.")
    return cleaned


def download_urls(urls: list[str], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    for index, url in enumerate(dict.fromkeys(urls), start=1):
        suffix = safe_suffix(url, ".bin")
        path = out_dir / f"fal_output_{timestamp}_{index:02d}{suffix}"
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        path.write_bytes(response.content)
        saved.append(path)

    return saved


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    parser = argparse.ArgumentParser(description="Run a fal.ai model and download returned media URLs.")
    parser.add_argument("--model", required=True, help="fal endpoint id, for example fal-ai/nano-banana-2")
    parser.add_argument("--args", help="Path to a JSON object with model arguments.")
    parser.add_argument("--set", action="append", default=[], help="Override/add one argument as key=value. JSON values are accepted.")
    parser.add_argument("--upload-file", action="append", default=[], help="Upload a local file and set one argument as key=path.")
    parser.add_argument("--out", default="Docs/MediaGeneration/outputs", help="Output folder for result JSON and media downloads.")
    parser.add_argument("--project", help="Optional project name. Outputs are saved in a subfolder under --out.")
    parser.add_argument("--no-download", action="store_true", help="Only save the JSON response.")
    parsed = parser.parse_args()

    if not os.environ.get("FAL_KEY"):
        print("FAL_KEY is not set. Set it before running paid fal requests.", file=sys.stderr)
        return 2

    try:
        import fal_client
    except ImportError:
        print("Missing dependency: fal-client. Install with: python -m pip install fal-client", file=sys.stderr)
        return 2

    arguments = load_arguments(parsed.args, parsed.set)
    apply_file_uploads(arguments, parsed.upload_file)
    out_dir = Path(parsed.out)
    if parsed.project:
        out_dir = out_dir / safe_project_name(parsed.project)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    print(f"Running {parsed.model} with arguments:")
    print(json.dumps(arguments, indent=2))

    request_id = ""

    def on_enqueue(enqueued_request_id: str) -> None:
        nonlocal request_id
        request_id = enqueued_request_id
        print(f"Queued fal request ID: {request_id}")

    try:
        result = fal_client.subscribe(
            parsed.model,
            arguments=arguments,
            with_logs=True,
            on_enqueue=on_enqueue,
        )
    except Exception as exc:
        error_path = out_dir / f"fal_error_{timestamp}.json"
        error_payload = {
            "model": parsed.model,
            "request_id": request_id,
            "arguments": arguments,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        error_path.write_text(json.dumps(error_payload, indent=2), encoding="utf-8")
        print(f"Saved error JSON: {error_path}", file=sys.stderr)
        if request_id:
            print(f"Recover with: python Python/scripts/media/fetch_fal_result.py --model {parsed.model} --request-id {request_id} --out {parsed.out}")
        raise

    result_path = out_dir / f"fal_result_{timestamp}.json"
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
