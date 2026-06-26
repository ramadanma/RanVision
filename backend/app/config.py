from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "mysql+aiomysql://ranvision:changeme@localhost:3306/ranvision"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev_secret_key_replace_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ENCRYPTION_KEY: str = ""
    HLS_SEGMENTS_DIR: str = "hls_segments"
    UPLOADS_DIR: str = "uploads"

    # Phase 2: ML inference
    YOLO_MODEL_PATH: str = "yolov8n-pose.pt"  # auto-downloaded on first run
    GPU_COUNT: int = 4                          # number of CUDA devices on server
    FACE_SIM_THRESHOLD: float = 0.35           # cosine similarity threshold (buffalo_l, normed embs)

    @property
    def uploads_videos(self) -> str:
        return f"{self.UPLOADS_DIR}/videos"

    @property
    def uploads_faces(self) -> str:
        return f"{self.UPLOADS_DIR}/faces"

    @property
    def uploads_zones(self) -> str:
        return f"{self.UPLOADS_DIR}/zones"


settings = Settings()
