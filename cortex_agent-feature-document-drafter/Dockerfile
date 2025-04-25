FROM python:3.12

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PROXY_HEADERS=1
ENV FORWARDED_ALLOW_IPS="*"
ENV TIMEOUT_KEEP_ALIVE=None

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application with streaming support
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--loop", "asyncio", "--port", "8080"]
