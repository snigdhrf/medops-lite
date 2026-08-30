"""Small smoke monitor for operational and input-quality checks."""

from __future__ import annotations

import argparse
import base64
import io
import json
import time
from pathlib import Path
from urllib import request

from PIL import Image, ImageEnhance


def encoded(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def invoke(url: str, payload: dict[str, str]) -> dict[str, object]:
    body = json.dumps(payload).encode()
    started = time.perf_counter()
    try:
        with request.urlopen(request.Request(url, data=body, headers={"Content-Type": "application/json"}), timeout=10) as response:
            result: object = json.loads(response.read())
        return {"ok": True, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "response": result}
    except Exception as error:  # smoke monitoring should record failures, not stop at the first one
        return {"ok": False, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error": str(error)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--url", default="http://localhost:8080/invocations")
    parser.add_argument("--output", default="monitoring-report.json")
    args = parser.parse_args()

    original = Image.open(args.image).convert("L")
    bright = ImageEnhance.Brightness(original).enhance(1.8)
    resized = original.resize((64, 64))
    checks = {
        "normal": invoke(args.url, {"image_base64": encoded(original)}),
        "brightness_shift": invoke(args.url, {"image_base64": encoded(bright)}),
        "unexpected_dimensions": invoke(args.url, {"image_base64": encoded(resized)}),
        "malformed_input": invoke(args.url, {"image_base64": "not-an-image"}),
    }
    Path(args.output).write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
