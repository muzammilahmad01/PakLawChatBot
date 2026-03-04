FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip insall --no-cache-dir -r requirements.txt

COPY ChatBot .

EXPOSE 5000

CMD ["uvicron", "api:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
