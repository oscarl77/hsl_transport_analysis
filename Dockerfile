# Official, lightweight Python base image optimized for production
FROM python:3.11-slim

# Set system environment variables
# PYTHONUNBUFFERED=1 forces logs to stream directly to the cloud terminal instantly
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create and set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for compiling certain wheel libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker's smart caching layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code packages into the application zone
COPY pipeline/ ./pipeline/
COPY run_pipeline.py .

# Create an explicit directory mount point for our persistent database volume
RUN mkdir -p /app/data

# 8. Define the container's boot command execution string
CMD ["python", "run_pipeline.py"]