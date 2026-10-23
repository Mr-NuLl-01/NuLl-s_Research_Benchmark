FROM python:3.12-slim
# Candidate runtime only. Never copy evaluator sources or expected outputs here.
RUN pip install --no-cache-dir numpy==2.3.5 scipy==1.17.0
ENV OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /task
