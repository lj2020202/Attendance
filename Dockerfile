FROM python:3.9

# Install system dependencies for face_recognition
RUN apt-get update && apt-get install -y \
    cmake \
    libgl1 \
    libglib2.0-0

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install -r requirements.txt

# Run app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
