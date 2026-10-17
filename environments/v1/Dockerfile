FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends gfortran libcairo2 fonts-dejavu-core ffmpeg \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy==2.3.5 scipy==1.17.0 matplotlib==3.10.8 Pillow==12.3.0 CairoSVG==2.8.2
ENV OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/matplotlib
WORKDIR /task
