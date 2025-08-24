FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY stream_binance.py stream_binance.py

CMD ["python", "stream_binance.py"]
