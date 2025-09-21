# ---- build stage: make a wheel ---------------------------------------------
FROM python:3.12-slim AS build

# System deps (optional: remove if don't need gcc for any deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Copy only files needed to resolve/install deps first (for better caching)
WORKDIR /app
COPY pyproject.toml ./
COPY README.md ./
# COPY LICENSE* ./   # uncomment if add a LICENSE file later

# Install build backend & build wheel
RUN python -m pip install --upgrade pip build && \
    python -m build --wheel --outdir /tmp/dist

# Now bring in the actual source and rebuild (wheel will be cached if unchanged)
COPY src ./src
RUN python -m build --wheel --outdir /tmp/dist

# ---- runtime stage: small image --------------------------------------------
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 10001 appuser
WORKDIR /home/appuser

# Copy wheel from builder and install it
COPY --from=build /tmp/dist/*.whl /tmp/
RUN python -m pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

# Default command: our CLI (exposed by pyproject [project.scripts])
USER appuser
ENTRYPOINT ["status-checker"]
CMD ["--format", "table"]

# --- to run as service instead, override CMD at runtime:
# docker run --rm -p 8080:8080 status-checker \
#   python -m uvicorn status_checker.serve:app --host 0.0.0.0 --port 8080
ENTRYPOINT ["python", "-m", "uvicorn", "status_checker.serve:app", "--host", "0.0.0.0", "--port", "8080"]
