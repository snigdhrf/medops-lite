import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest
import torch

from src.model import PneumoniaCNN


def test_sagemaker_serve_command_starts_http_server(tmp_path):
    model_path = tmp_path / "model.pt"
    torch.save(PneumoniaCNN().state_dict(), model_path)

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    process = subprocess.Popen(
        [sys.executable, "-m", "src.predict", "serve", "--model", str(model_path), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(process.stdout.read())
            try:
                with urlopen(f"http://127.0.0.1:{port}/ping", timeout=0.2) as response:
                    assert response.status == 200
                    break
            except URLError:
                time.sleep(0.05)
        else:
            pytest.fail("server did not become healthy within 5 seconds")

        for payload in (b"null", b"[1, 2]", b'{"image_base64": 123}'):
            request = Request(
                f"http://127.0.0.1:{port}/invocations",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with pytest.raises(HTTPError) as error:
                urlopen(request, timeout=1)
            assert error.value.code == 400
    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
