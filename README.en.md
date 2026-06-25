# RanVision

Intelligent Video Surveillance System

## Project Overview

RanVision is a powerful intelligent video surveillance and analytics platform supporting real-time video stream processing, facial recognition, region intrusion detection, dwell time analysis, posture detection, and other AI analysis features.

### Technology Stack

**Backend**
- Python 3.11 + FastAPI
- SQLAlchemy + Alembic (database migrations)
- Redis (caching and state management)
- FFmpeg (video stream processing/HLS)

**Frontend**
- React 18 + TypeScript
- Ant Design 5.0
- HLS.js (video playback)

## Features

### Video Source Management
- RTSP video stream ingestion
- Real-time HLS video output
- Toggle video overlay
- Toggle facial recognition

### Intelligent Analysis
- **Region Intrusion Detection**: Customizable polygonal monitoring zones
- **Dwell Detection**: Alerts for prolonged person presence
- **Posture Analysis**: Detect postures such as raising hands or falling
- **Facial Recognition**: Support uploading face libraries for identity recognition

### Alert System
- Multiple alert methods: Email, Webhook
- Alert rule configuration
- Trigger record querying

### User Management
- User registration/login
- JWT token authentication
- Data isolation protection

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis
- FFmpeg

### Backend Configuration

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit the .env file to configure database, Redis, and other parameters
```

3. Start the service:
```bash
# Using Docker
docker-compose up -d

# Or manually start
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Configuration

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

## API Documentation

After starting the backend service, visit: `http://localhost:8000/docs`

### Main Endpoints

| Module | Endpoint | Description |
|--------|----------|-------------|
| Authentication | POST /api/auth/register | User registration |
| Authentication | POST /api/auth/login | User login |
| Video Sources | GET/POST /api/sources | List/create video sources |
| Video Sources | POST /api/sources/{id}/start | Start video stream |
| Zones | GET/POST /api/zones | Manage monitoring zones |
| Rules | GET/POST /api/rules | Manage alert rules |
| Faces | GET/POST /api/faces | Manage face library |
| Records | GET /api/records | Query trigger records |

## Project Structure

```
RanVision/
├── backend/
│   ├── app/
│   │   ├── config.py      # Configuration management
│   │   ├── database.py   # Database connection
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/     # API routes
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── worker/       # Video processing worker
│   └── alembic/          # Database migrations
├── frontend/
│   └── src/
│       ├── api/         # API client
│       ├── components/  # React components
│       ├── pages/        # Page components
│       └── store/       # State management
└── docker-compose.yml   # Docker configuration
```

## License

MIT License