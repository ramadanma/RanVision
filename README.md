# RanVision

Intelligent Video Surveillance & AI Analytics Platform

[中文](README.cn.md)

---

## Overview

RanVision is a self-hosted video surveillance platform that combines real-time video streaming with AI-powered behavioral analysis. Define polygon zones on any camera feed, attach rules (dwell time, limb angle), and receive instant email or webhook alerts when a rule fires — complete with snapshot evidence.

**Key capabilities**

- Real-time RTSP/file ingestion with HLS output and WebSocket JPEG push
- YOLOv8-Pose person detection + ByteTrack multi-person tracking
- InsightFace `buffalo_l` face recognition with per-track identity stabilization
- Configurable detection zones and behavioral rules per source
- Automatic report delivery (email / HTTP webhook) with customizable templates
- Multi-GPU aware: each source worker runs on a dedicated CUDA device
- Bilingual UI — English and Chinese

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy (async), Alembic |
| Database | MySQL 8 |
| Cache | Redis 7 |
| Video | FFmpeg → HLS, OpenCV, WebSocket |
| ML Inference | Ultralytics YOLOv8-Pose, InsightFace `buffalo_l` |
| Frontend | React 18, TypeScript, Ant Design 5, HLS.js |
| Auth | JWT (python-jose) |

---

## Features

### Video Sources
- Add IP cameras (RTSP) or upload local video files
- Adjustable RTSP transport (TCP/UDP)
- Start / stop processing per source
- Live preview via HLS player or WebSocket stream
- Toggle skeleton overlay and detection ROI

### Detection Zones
- Draw freeform polygon zones directly on the video frame
- Multiple zones per source, each with independent rules

### Behavioral Rules
| Rule Type | Description |
|-----------|-------------|
| `dwell_time` | Trigger when a person stays inside a zone longer (or shorter) than N seconds |
| `limb_angle` | Trigger when the elbow angle of the left/right arm exceeds a threshold (raised arm, falling) |

### Face Recognition
- Upload face photos; embeddings are extracted automatically with InsightFace
- Per-track identity stabilized over a 20-frame rolling history
- Optional **front-facing filter**: back-facing persons are skipped entirely — no identity assignment and no rule triggers

### Report & Alert System
- Multiple report configs per source, each linked to specific rules
- Delivery methods: **Email** (SMTP) or **HTTP Webhook**
- Customizable subject / body templates with variables: `{{person_name}}`, `{{zone_id}}`, `{{rule_id}}`, `{{triggered_at}}`, `{{details}}`
- Configurable snapshot count attached to each alert (pulled from Redis frame buffer)
- Trigger records stored in the database for audit / review

### Architecture: Three-Thread Worker per Source
Each running source spawns three coordinated threads to prevent any single stage from stalling the others:

```
reader thread    — cap.read() + frame_buffer push   (display is never blocked by GPU)
inference thread — YOLO + InsightFace + rule engine  (always works on the latest frame)
trigger thread   — DB write + alert delivery         (I/O never blocks inference)
```

---

## Prerequisites

| Requirement | Minimum |
|-------------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| CUDA | 11.8+ (optional, CPU fallback available) |
| FFmpeg | Any recent version |
| Docker & Docker Compose | For MySQL + Redis |

> **YOLO model**: `yolov8n-pose.pt` is downloaded automatically by Ultralytics on first run.  
> **InsightFace model**: `buffalo_l` is downloaded automatically on first run.

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/ramadanma/RanVision.git
cd RanVision
cp docker-compose.example.yml docker-compose.yml
# Edit docker-compose.yml — adjust host port mappings if needed
```

Create `backend/.env`:

```env
DATABASE_URL=mysql+aiomysql://ranvision:changeme@127.0.0.1:3307/ranvision
REDIS_URL=redis://:your_redis_password@127.0.0.1:6381/0
SECRET_KEY=replace_with_a_long_random_string
ENCRYPTION_KEY=replace_with_fernet_key          # generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# MySQL credentials (must match docker-compose.yml)
MYSQL_USER=ranvision
MYSQL_PASSWORD=changeme
MYSQL_DATABASE=ranvision
MYSQL_ROOT_PASSWORD=rootchangeme
REDIS_PASSWORD=your_redis_password

# ML settings
YOLO_MODEL_PATH=yolov8n-pose.pt   # or yolov8s-pose.pt for better accuracy
GPU_COUNT=1                        # number of CUDA GPUs; 0 = CPU only
FACE_SIM_THRESHOLD=0.35            # cosine similarity threshold for face recognition
```

### 2. Start infrastructure

```bash
docker-compose up -d   # starts MySQL 8 + Redis 7
```

### 3. Set up the backend

```bash
cd backend
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Set up the frontend

```bash
cd frontend
npm install
npm run dev       # development server on http://localhost:5173
# or
npm run build     # production build → dist/
```

### 5. Open the app

Navigate to `http://localhost:5173`, register an account, add a video source, and start.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `mysql+aiomysql://...` | Async SQLAlchemy connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `SECRET_KEY` | `dev_secret_key_replace_in_production` | JWT signing key |
| `ENCRYPTION_KEY` | _(empty)_ | Fernet key for encrypting camera passwords |
| `HLS_SEGMENTS_DIR` | `hls_segments` | Directory for HLS `.m3u8` / `.ts` files |
| `UPLOADS_DIR` | `uploads` | Directory for uploaded videos and face photos |
| `YOLO_MODEL_PATH` | `yolov8n-pose.pt` | Path or filename of the YOLO pose model |
| `GPU_COUNT` | `4` | Number of CUDA devices; source N uses `cuda:(N % GPU_COUNT)` |
| `FACE_SIM_THRESHOLD` | `0.35` | Minimum cosine similarity to accept a face match |

---

## API Documentation

Interactive docs are available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc` after starting the backend.

### Endpoint Summary

| Module | Method | Path | Description |
|--------|--------|------|-------------|
| Auth | POST | `/api/auth/register` | Register a new user |
| Auth | POST | `/api/auth/login` | Login and receive JWT |
| Sources | GET/POST | `/api/sources` | List / create video sources |
| Sources | POST | `/api/sources/{id}/start` | Start processing a source |
| Sources | POST | `/api/sources/{id}/stop` | Stop processing a source |
| Zones | GET/POST | `/api/zones` | List / create detection zones |
| Rules | GET/POST | `/api/rules` | List / create behavioral rules |
| Faces | GET/POST | `/api/faces` | List / upload face photos |
| Report Configs | GET/POST | `/api/report-configs` | List / create report configurations |
| Records | GET | `/api/records` | Query trigger history |
| Stream | WS | `/api/stream/{id}/ws?token=...` | WebSocket live JPEG stream |
| Stream | GET | `/api/stream/{id}/index.m3u8` | HLS manifest |

---

## Project Structure

```
RanVision/
├── backend/
│   ├── app/
│   │   ├── config.py          # Settings (pydantic-settings + .env)
│   │   ├── database.py        # Async SQLAlchemy engine & session
│   │   ├── models/            # ORM models
│   │   ├── routers/           # FastAPI routers
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── worker/
│   │       ├── stream_processor.py   # Three-thread worker per source
│   │       ├── yolo_stub.py          # YOLOv8-Pose inference + ByteTrack
│   │       ├── insightface_stub.py   # InsightFace recognition
│   │       └── rule_engine.py        # Behavioral rule evaluation
│   └── alembic/               # Database migration scripts
├── frontend/
│   └── src/
│       ├── api/               # Axios API client
│       ├── components/        # Reusable React components
│       ├── pages/             # Route-level page components
│       └── store/             # Zustand state management
├── docker-compose.example.yml # Template — copy to docker-compose.yml
└── tmp/
    └── demo.py                # Reference implementation
```

---

## License

MIT License
