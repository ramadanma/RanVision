# ─────────────────────────────────────────────────────────────
# Phase 1（无 GPU 推理）：使用轻量 Python 镜像
FROM python:3.11-slim AS base-cpu

# Phase 2（启用 YOLO + InsightFace）：注释掉上面一行，取消注释下面一行
# CUDA 版本须与宿主机驱动对齐（Tesla T4 支持 CUDA 12.x）
# FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 AS base-cpu
# ─────────────────────────────────────────────────────────────

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf python3 /usr/bin/python \
    && ln -sf pip3 /usr/bin/pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p hls_segments uploads/videos uploads/faces uploads/zones

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
