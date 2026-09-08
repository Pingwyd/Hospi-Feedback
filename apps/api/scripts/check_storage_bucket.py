"""One-off local check: storage bucket accepts upload after config.toml registration."""

from __future__ import annotations

import io
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    status = json.loads(
        subprocess.check_output(
            ["supabase", "status", "--output", "json"],
            cwd=REPO_ROOT,
            text=True,
        )
    )
    url = status["API_URL"]
    key = status["SERVICE_ROLE_KEY"]
    bucket = "report-attachments"
    image = Image.new("RGB", (2, 2), color="red")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data = buffer.getvalue()
    object_path = "diagnostic/test-upload.png"
    req_url = f"{url.rstrip('/')}/storage/v1/object/{bucket}/{object_path}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "image/png",
        "x-upsert": "true",
    }
    req = urllib.request.Request(req_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"OK HTTP {resp.status}")
            return 0
    except urllib.error.HTTPError as exc:
        print(f"FAIL HTTP {exc.code}")
        print(exc.read().decode("utf-8", errors="replace"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
