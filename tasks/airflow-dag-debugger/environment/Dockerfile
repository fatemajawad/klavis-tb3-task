FROM python:3.11-slim

RUN pip install --no-cache-dir apache-airflow==2.8.1

WORKDIR /workspace

COPY dags/ /workspace/dags/

CMD ["/bin/bash"]
