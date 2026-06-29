FROM python:3.11-slim

RUN pip install --no-cache-dir dbt-duckdb==1.8.1

WORKDIR /workspace

COPY dbt_project/ /workspace/dbt_project/

CMD ["/bin/bash"]
