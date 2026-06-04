FROM python:3.12-slim

WORKDIR /app

# Install basic system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Astral uv for modern, fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy requirements/project definitions
COPY pyproject.toml ./

# Install project dependencies. Since we have a workspace setup, we sync or pip install.
# Using 'uv pip install --system' is suitable for a single-app container without nesting venvs.
RUN uv pip install --system --no-cache . || uv pip install --system --no-cache -r requirements.txt || true

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p vectorstore data logs corpus

# Expose Streamlit default port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
