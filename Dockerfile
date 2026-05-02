FROM python:3.9

RUN apt-get update && apt-get install -y \
    cmake \
    libgl1 \
    libglib2.0-0

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD gunicorn app:app --bind 0.0.0.0:$PORT
