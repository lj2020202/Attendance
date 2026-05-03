# Use Python 3.11
FROM python:3.11-slim

# Install modern system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-6 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
# We use --no-cache-dir to save space and ensure a fresh install
RUN pip install --no-cache-dir dlib==19.24.1
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Start the app
CMD ["python", "app.py"]
