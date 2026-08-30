FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src

EXPOSE 8080
ENTRYPOINT ["/app/.venv/bin/python", "-m", "src.predict"]
CMD ["--serve", "--model", "/opt/ml/model/model.pt"]
