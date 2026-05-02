FROM python:3.9-slim

# Install system dependencies (IMPORTANT for dlib)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip

# Install numpy FIRST (prevents dlib crash)
RUN pip install numpy

# Install requirements
RUN pip install -r requirements.txt

# Railway port fix
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]
