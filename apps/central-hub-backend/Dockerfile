FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY apps/central-hub-backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy source codes
COPY apps/central-hub-backend /app
COPY bot /bot

# Expose PYTHONPATH
ENV PYTHONPATH=/app:/bot/document-processing

# Default command runs uvicorn server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
