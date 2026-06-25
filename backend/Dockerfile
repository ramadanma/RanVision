# ─────────────────────────────────────────────────────────────
# Phase 1（无 GPU 推理）：使用轻量 Python 镜像
FROM python:3.11-slim

# Phase 2（启用 YOLO + InsightFace）：注释掉上面一行，取消注释下面两行
# CUDA 版本须与宿主机驱动对齐（Tesla T4 支持 CUDA 12.x）
# FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04
# RUN apt-get update && apt-get install -y python3 python3-pip && ln -sf python3 /usr/bin/python && ln -sf pip3 /usr/bin/pip
# ─────────────────────────────────────────────────────────────

# 切换 apt 源为阿里云镜像（解决无法访问 deb.debian.org 的问题）
# 兼容 Debian 12(sources.list) 和 Debian 13(sources.list.d/*.sources 的 DEB822 格式)
RUN if [ -f /etc/apt/sources.list ]; then \
        sed -i \
            's|http://deb.debian.org/debian|http://mirrors.aliyun.com/debian|g; \
             s|http://security.debian.org|http://mirrors.aliyun.com/debian-security|g; \
             s|http://deb.debian.org/debian-security|http://mirrors.aliyun.com/debian-security|g' \
            /etc/apt/sources.list; \
    fi && \
    find /etc/apt/sources.list.d/ -name "*.sources" -exec sed -i \
        's|http://deb.debian.org/debian|http://mirrors.aliyun.com/debian|g; \
         s|http://security.debian.org|http://mirrors.aliyun.com/debian-security|g; \
         s|http://deb.debian.org/debian-security|http://mirrors.aliyun.com/debian-security|g' \
        {} \; 2>/dev/null || true

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 使用阿里云镜像
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p hls_segments uploads/videos uploads/faces uploads/zones

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
