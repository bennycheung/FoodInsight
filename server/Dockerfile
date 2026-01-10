FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .

# Install dependencies
RUN uv pip install --system .

# Copy application code
COPY app/ app/

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
