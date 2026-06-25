# RanVision

智能视频监控系统 | Intelligent Video Surveillance System

## 项目简介

RanVision 是一个功能强大的智能视频监控与分析平台，支持实时视频流处理、人脸识别、区域入侵检测、停留时间分析、姿态检测等多种 AI 分析功能。

### 技术栈

**后端**
- Python 3.11 + FastAPI
- SQLAlchemy + Alembic (数据库迁移)
- Redis (缓存与状态管理)
- FFmpeg (视频流处理/HLS)

**前端**
- React 18 + TypeScript
- Ant Design 5.0
- HLS.js (视频播放)

## 功能特性

### 视频源管理
- RTSP 视频流接入
- 实时 HLS 视频输出
- 视频叠加层开关
- 人脸识别开关

### 智能分析
- **区域入侵检测**: 自定义多边形监控区域
- **停留检测**: 人员停留时间告警
- **姿态分析**: 检测人员举手/跌倒等姿态
- **人脸识别**: 支持上传人脸库进行身份识别

### 告警系统
- 多种告警方式：邮件、Webhook
- 告警规则配置
- 触发记录查询

### 用户管理
- 用户注册/登录
- JWT 令牌认证
- 数据隔离保护

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Redis
- FFmpeg

### 后端配置

1. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、Redis 等参数
```

3. 启动服务：
```bash
# 使用 Docker
docker-compose up -d

# 或手动启动
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端配置

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

## API 文档

启动后端服务后访问: `http://localhost:8000/docs`

### 主要接口

| 模块 | 接口路径 | 说明 |
|------|----------|------|
| 认证 | POST /api/auth/register | 用户注册 |
| 认证 | POST /api/auth/login | 用户登录 |
| 视频源 | GET/POST /api/sources | 视频源列表/创建 |
| 视频源 | POST /api/sources/{id}/start | 启动视频流 |
| 区域 | GET/POST /api/zones | 监控区域管理 |
| 规则 | GET/POST /api/rules | 告警规则管理 |
| 人脸 | GET/POST /api/faces | 人脸库管理 |
| 记录 | GET /api/records | 触发记录查询 |

## 项目结构

```
RanVision/
├── backend/
│   ├── app/
│   │   ├── config.py      # 配置管理
│   │   ├── database.py   # 数据库连接
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── routers/     # API 路由
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/    # 业务逻辑
│   │   └── worker/       # 视频处理 worker
│   └── alembic/          # 数据库迁移
├── frontend/
│   └── src/
│       ├── api/         # API 客户端
│       ├── components/  # React 组件
│       ├── pages/        # 页面组件
│       └── store/       # 状态管理
└── docker-compose.yml   # Docker 配置
```

## 许可证

MIT License