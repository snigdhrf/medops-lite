"""CLI and minimal SageMaker-compatible HTTP inference server."""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import torch
from PIL import Image

from .data import image_to_tensor
from .model import PneumoniaCNN


def load_model(path: str) -> PneumoniaCNN:
    model = PneumoniaCNN()
    state = torch.load(path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model


def predict_bytes(model: PneumoniaCNN, image_bytes: bytes) -> dict[str, object]:
    image = Image.open(io.BytesIO(image_bytes))
    with torch.no_grad():
        probabilities = torch.softmax(model(image_to_tensor(image).unsqueeze(0)), dim=1)[0]
    label = int(probabilities.argmax())
    return {"label": label, "class": "pneumonia" if label else "normal", "confidence": float(probabilities[label])}


class Handler(BaseHTTPRequestHandler):
    model: PneumoniaCNN | None = None

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/ping":
            self.send_response(200 if self.model else 503)
            self.end_headers()
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/invocations" or self.model is None:
            self.send_error(404)
            return
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            image_bytes = base64.b64decode(payload["image_base64"])
            response = predict_bytes(self.model, image_bytes)
            encoded = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        except (KeyError, TypeError, ValueError, OSError) as error:
            self.send_error(400, str(error))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", nargs="?")
    parser.add_argument("--model", default=os.getenv("MODEL_PATH", "artifacts/model.pt"))
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    if args.serve or args.image == "serve":
        Handler.model = load_model(args.model)
        HTTPServer(("0.0.0.0", args.port), Handler).serve_forever()
    elif args.image:
        print(json.dumps(predict_bytes(load_model(args.model), open(args.image, "rb").read())))
    else:
        parser.error("provide an image or --serve")


if __name__ == "__main__":
    main()
