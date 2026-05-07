"""Minimal fal.ai Kandinsky text-to-video smoke test.

This intentionally follows fal's Python queue pattern:
submit -> status loop -> get result -> download result["video"]["url"].
"""

from __future__ import annotations

import json
import os
import sys
import time
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL = "fal-ai/kandinsky5/text-to-video/distill"
OUT_DIR = PROJECT_ROOT / "Docs" / "MediaGeneration" / "outputs" / "text_to_video"
PROMPT = (
    "A calm 5 second cinematic shot of a single glowing glass cube floating above "
    "a dark studio floor. Slow dolly-in camera movement, soft reflections, clean "
    "composition, no text, no logo, no people."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal fal.ai Kandinsky text-to-video smoke test.")
    parser.add_argument("--submit-only", action="store_true", help="Submit the job, save request info, then exit.")
    parser.add_argument("--poll-seconds", type=float, default=5, help="Seconds between status checks.")
    parser.add_argument("--max-wait-seconds", type=float, default=900, help="Maximum time to wait before exiting.")
    parsed = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env", override=False)
    if not os.environ.get("FAL_KEY"):
        print("FAL_KEY is missing. Put it in the project .env file.", file=sys.stderr)
        return 2

    import fal_client

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    arguments = {
        "prompt": PROMPT,
        "resolution": "768x512",
        "aspect_ratio": "3:2",
        "duration": "5s",
    }

    print(f"Submitting to {MODEL}")
    print(json.dumps(arguments, indent=2))

    handler = fal_client.submit(MODEL, arguments=arguments)
    request_id = getattr(handler, "request_id", "")
    print(f"Request ID: {request_id}")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    request_path = OUT_DIR / f"kandinsky_request_{timestamp}_{request_id}.json"
    request_path.write_text(
        json.dumps(
            {
                "model": MODEL,
                "request_id": request_id,
                "arguments": arguments,
                "submitted_at": timestamp,
                "fetch_command": (
                    "uv run python Python/scripts/media/fetch_fal_result.py "
                    f"--model {MODEL} --request-id {request_id} "
                    "--out Docs/MediaGeneration/outputs/text_to_video"
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved request info: {request_path}")

    if parsed.submit_only:
        print("Submitted only. Fetch later with:")
        print(
            "uv run python Python/scripts/media/fetch_fal_result.py "
            f"--model {MODEL} --request-id {request_id} "
            "--out Docs/MediaGeneration/outputs/text_to_video"
        )
        return 0

    started = time.monotonic()
    while True:
        elapsed = time.monotonic() - started
        if elapsed > parsed.max_wait_seconds:
            print(f"Timed out locally after {parsed.max_wait_seconds}s.")
            print("The FAL job may still finish. Fetch later with:")
            print(
                "uv run python Python/scripts/media/fetch_fal_result.py "
                f"--model {MODEL} --request-id {request_id} "
                "--out Docs/MediaGeneration/outputs/text_to_video"
            )
            return 3

        status = handler.status(with_logs=True)

        if isinstance(status, fal_client.Queued):
            print(f"[{elapsed:.0f}s] Queued. Position: {status.position}")
        elif isinstance(status, fal_client.InProgress):
            print(f"[{elapsed:.0f}s] In progress...")
            for log in status.logs or []:
                message = log.get("message") if isinstance(log, dict) else str(log)
                if message:
                    print(message)
        elif isinstance(status, fal_client.Completed):
            print(f"[{elapsed:.0f}s] Completed. Metrics: {status.metrics}")
            break
        else:
            print(f"[{elapsed:.0f}s] Status: {status}")

        time.sleep(parsed.poll_seconds)

    result = handler.get()
    result_path = OUT_DIR / f"kandinsky_result_{timestamp}_{request_id}.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved JSON: {result_path}")

    video = result.get("video") if isinstance(result, dict) else None
    video_url = video.get("url") if isinstance(video, dict) else None
    if not video_url:
        print("No result['video']['url'] found.")
        print(json.dumps(result, indent=2))
        return 1

    suffix = Path(video.get("file_name") or "output.mp4").suffix or ".mp4"
    video_path = OUT_DIR / f"kandinsky_smoke_{timestamp}_{request_id}{suffix}"
    response = requests.get(video_url, timeout=180)
    response.raise_for_status()
    video_path.write_bytes(response.content)
    print(f"Downloaded video: {video_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
