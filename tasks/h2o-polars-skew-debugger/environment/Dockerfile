FROM python:3.11-slim

RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pandas==2.2.2 \
    polars==0.20.31 \
    scikit-learn==1.4.2

WORKDIR /workspace

COPY pipeline/ /workspace/pipeline/
RUN touch /workspace/pipeline/__init__.py

CMD ["/bin/bash"]
