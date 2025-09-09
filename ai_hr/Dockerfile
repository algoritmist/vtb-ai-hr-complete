FROM python:3.11-slim

WORKDIR /app
RUN apt-get update
RUN apt-get install ffmpeg -y

COPY requirements.txt .

RUN pip install -r requirements.txt
COPY . .

EXPOSE 9300

ENTRYPOINT [ "python", "main.py" ]
