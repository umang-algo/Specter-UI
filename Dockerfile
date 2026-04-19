# Use the official Microsoft Playwright image which includes all necessary browsers and dependencies
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Install Playwright browsers (though they should be in the base image, this ensures they are linked)
RUN playwright install chromium

# Expose the dashboard port
EXPOSE 8765

# Setup environment variables defaults
ENV PYTHONUNBUFFERED=1
ENV PORT=8765

# Start the dashboard and the orchestrator
# Note: In production, you might want to run this as a webhook listener.
CMD ["python3", "run.py"]
