# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Bring in the uv binary from the official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Install locked runtime dependencies (no dev group in the image).
COPY pyproject.toml uv.lock README.md .python-version ./
COPY src ./src
RUN uv sync --frozen --no-dev

EXPOSE 9000

CMD ["uv", "run", "--no-dev", "kitoboy-mcp"]
