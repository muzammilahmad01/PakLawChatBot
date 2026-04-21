FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir torch --index-url \
    https://download.pytorch.org/whl/cpu

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY ChatBot/ .

EXPOSE 5000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "5000"]
