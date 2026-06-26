# RanVision

智能视频监控与 AI 行为分析平台

[English](README.md)

---

## 概述

RanVision 是一套自托管视频监控平台，将实时视频流与 AI 行为分析深度融合。在任意摄像头画面上绘制多边形区域，配置规则（停留时长、肢体角度），一旦规则触发即可立即收到邮件或 Webhook 警报，并附带快照证据。

**核心能力**

- 实时 RTSP/文件接入，输出 HLS 流与 WebSocket JPEG 推流
- YOLOv8-Pose 人体检测 + ByteTrack 多目标跟踪
- InsightFace `buffalo_l` 人脸识别，具备逐轨迹身份稳定机制
- 每路视频源可独立配置检测区域与行为规则
- 自动发送报告（邮件 / HTTP Webhook），支持自定义模板
- 多 GPU 感知：每路视频源工作线程独占一块 CUDA 设备
- 双语界面 —— 中文与英文

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11、FastAPI、SQLAlchemy（异步）、Alembic |
| 数据库 | MySQL 8 |
| 缓存 | Redis 7 |
| 视频 | FFmpeg → HLS、OpenCV、WebSocket |
| ML 推理 | Ultralytics YOLOv8-Pose、InsightFace `buffalo_l` |
| 前端 | React 18、TypeScript、Ant Design 5、HLS.js |
| 鉴权 | JWT（python-jose）|

---

## 功能特性

### 视频源

- 添加 IP 摄像头（RTSP）或上传本地视频文件
- 可调整 RTSP 传输协议（TCP/UDP）
- 按视频源单独启动 / 停止处理
- 通过 HLS 播放器或 WebSocket 流实时预览
- 切换骨架叠加层与检测 ROI 显示

### 检测区域

- 在视频帧上直接绘制自由多边形区域
- 每路视频源支持多个区域，各区域独立配置规则

### 行为规则

| 规则类型 | 描述 |
|----------|------|
| `dwell_time` | 人员在区域内停留时间超过（或短于）N 秒时触发 |
| `limb_angle` | 左臂或右臂肘关节角度超过阈值时触发（举手、跌倒等） |

### 人脸识别

- 上传人脸照片，InsightFace 自动提取特征嵌入
- 基于 20 帧滚动历史对每条轨迹稳定身份
- 可选**仅正面过滤**：背对摄像头的人员会被完全跳过，不进行身份识别，也不触发规则

### 报告与告警系统

- 每路视频源可配置多个报告配置，每个配置关联特定规则
- 发送方式：**邮件**（SMTP）或 **HTTP Webhook**
- 支持自定义主题 / 正文模板，可用变量：`{{person_name}}`、`{{zone_id}}`、`{{rule_id}}`、`{{triggered_at}}`、`{{details}}`
- 每条告警可附带指定数量的快照（从 Redis 帧缓冲区提取）
- 触发记录存入数据库，便于审计与回溯

### 架构：每路视频源三线程工作模式

每路运行中的视频源会启动三个协同工作的线程，确保任一阶段阻塞不会影响其他阶段：

```
reader 线程    — cap.read() + frame_buffer 推送   （显示永不被 GPU 阻塞）
inference 线程 — YOLO + InsightFace + 规则引擎    （始终处理最新帧）
trigger 线程   — 数据库写入 + 告警发送             （I/O 永不阻塞推理）
```

---

## 环境要求

| 依赖项 | 最低版本 |
|--------|----------|
| Python | 3.11+ |
| Node.js | 18+ |
| CUDA | 11.8+（可选，支持 CPU 回退）|
| FFmpeg | 任意近期版本 |
| Docker & Docker Compose | 用于 MySQL + Redis |

> **YOLO 模型**：`yolov8n-pose.pt` 首次运行时由 Ultralytics 自动下载。  
> **InsightFace 模型**：`buffalo_l` 首次运行时自动下载。

---

## 快速开始

### 1. 克隆并配置

```bash
git clone https://github.com/your-org/RanVision.git
cd RanVision
cp docker-compose.example.yml docker-compose.yml
# 编辑 docker-compose.yml — 按需调整主机端口映射
```

创建 `backend/.env`：

```env
DATABASE_URL=mysql+aiomysql://ranvision:changeme@127.0.0.1:3307/ranvision
REDIS_URL=redis://:your_redis_password@127.0.0.1:6381/0
SECRET_KEY=replace_with_a_long_random_string
ENCRYPTION_KEY=replace_with_fernet_key          # 生成方式：python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# MySQL 凭据（须与 docker-compose.yml 保持一致）
MYSQL_USER=ranvision
MYSQL_PASSWORD=changeme
MYSQL_DATABASE=ranvision
MYSQL_ROOT_PASSWORD=rootchangeme
REDIS_PASSWORD=your_redis_password

# ML 配置
YOLO_MODEL_PATH=yolov8n-pose.pt   # 或 yolov8s-pose.pt（精度更高）
GPU_COUNT=1                        # CUDA GPU 数量；0 = 仅 CPU
FACE_SIM_THRESHOLD=0.35            # 人脸识别余弦相似度阈值
```

### 2. 启动基础设施

```bash
docker-compose up -d   # 启动 MySQL 8 + Redis 7
```

### 3. 配置后端

```bash
cd backend
pip install -r requirements.txt

# 执行数据库迁移
alembic upgrade head

# 启动 API 服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 配置前端

```bash
cd frontend
npm install
npm run dev       # 开发服务器，访问 http://localhost:5173
# 或
npm run build     # 生产构建 → dist/
```

### 5. 打开应用

访问 `http://localhost:5173`，注册账号，添加视频源，即可开始使用。

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `mysql+aiomysql://...` | 异步 SQLAlchemy 连接字符串 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 URL |
| `SECRET_KEY` | `dev_secret_key_replace_in_production` | JWT 签名密钥 |
| `ENCRYPTION_KEY` | _（空）_ | 用于加密摄像头密码的 Fernet 密钥 |
| `HLS_SEGMENTS_DIR` | `hls_segments` | HLS `.m3u8` / `.ts` 文件目录 |
| `UPLOADS_DIR` | `uploads` | 上传视频与人脸照片的存储目录 |
| `YOLO_MODEL_PATH` | `yolov8n-pose.pt` | YOLO 姿态模型路径或文件名 |
| `GPU_COUNT` | `4` | CUDA 设备数量；第 N 路视频源使用 `cuda:(N % GPU_COUNT)` |
| `FACE_SIM_THRESHOLD` | `0.35` | 接受人脸匹配的最低余弦相似度 |

---

## API 文档

启动后端后，交互式文档可在 `http://localhost:8000/docs`（Swagger UI）和 `http://localhost:8000/redoc` 访问。

### 接口概览

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 鉴权 | POST | `/api/auth/register` | 注册新用户 |
| 鉴权 | POST | `/api/auth/login` | 登录并获取 JWT |
| 视频源 | GET/POST | `/api/sources` | 列出 / 创建视频源 |
| 视频源 | POST | `/api/sources/{id}/start` | 启动视频源处理 |
| 视频源 | POST | `/api/sources/{id}/stop` | 停止视频源处理 |
| 检测区域 | GET/POST | `/api/zones` | 列出 / 创建检测区域 |
| 规则 | GET/POST | `/api/rules` | 列出 / 创建行为规则 |
| 人脸 | GET/POST | `/api/faces` | 列出 / 上传人脸照片 |
| 报告配置 | GET/POST | `/api/report-configs` | 列出 / 创建报告配置 |
| 触发记录 | GET | `/api/records` | 查询触发历史 |
| 流媒体 | WS | `/api/stream/{id}/ws?token=...` | WebSocket 实时 JPEG 推流 |
| 流媒体 | GET | `/api/stream/{id}/index.m3u8` | HLS 清单文件 |

---

## 项目结构

```
RanVision/
├── backend/
│   ├── app/
│   │   ├── config.py          # 配置（pydantic-settings + .env）
│   │   ├── database.py        # 异步 SQLAlchemy 引擎与会话
│   │   ├── models/            # ORM 模型
│   │   ├── routers/           # FastAPI 路由
│   │   ├── schemas/           # Pydantic 模式
│   │   ├── services/          # 业务逻辑
│   │   └── worker/
│   │       ├── stream_processor.py   # 每路视频源三线程工作器
│   │       ├── yolo_stub.py          # YOLOv8-Pose 推理 + ByteTrack
│   │       ├── insightface_stub.py   # InsightFace 人脸识别
│   │       └── rule_engine.py        # 行为规则评估
│   └── alembic/               # 数据库迁移脚本
├── frontend/
│   └── src/
│       ├── api/               # Axios API 客户端
│       ├── components/        # 可复用 React 组件
│       ├── pages/             # 路由级页面组件
│       └── store/             # Zustand 状态管理
├── docker-compose.example.yml # 模板 — 复制为 docker-compose.yml 后使用
└── tmp/
    └── demo.py                # 参考实现
```

---

## 许可证

MIT License
