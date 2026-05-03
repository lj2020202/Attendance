# Use a Python image that already has some build tools
FROM python:3.11-slim

# Install system dependencies required for dlib and face_recognition
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy your requirements file
COPY requirements.txt .

# Install Python dependencies
# Note: we install dlib separately first because it takes a long time to compile
RUN pip install --no-cache-dir dlib==19.24.1
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Start the application
CMD ["python", "app.py"]
