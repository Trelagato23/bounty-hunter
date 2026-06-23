# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
# Adding libnotify-bin for n8n to potentially trigger desktop/system notifications
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libnotify-bin \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pyyaml requests beautifulsoup4 schedule pandas sqlalchemy

# Copy project
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/data /app/reports /app/logs

# Run the application
# Default to running a priority 1 scrape
CMD ["python", "bounty_hunter.py", "--scrape", "--priority", "1"]
