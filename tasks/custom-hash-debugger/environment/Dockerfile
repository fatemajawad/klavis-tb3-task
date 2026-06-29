FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir setuptools

WORKDIR /workspace

COPY src/ /workspace/src/
COPY setup.py /workspace/setup.py

CMD ["/bin/bash"]
