FROM python:3.11-slim

RUN pip install --no-cache-dir duckdb==0.10.3

COPY verify.py /verify.py

CMD ["python3", "/verify.py"]
