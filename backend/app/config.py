from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    postgres_url: str = "postgresql://postgres:postgres@postgres:5432/openclaims"
    redis_url: str = "redis://redis:6379/0"
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # GCP and Gemini configurations
    gcp_project_id: Optional[str] = None
    gcs_bucket_name: Optional[str] = None
    local_storage_path: str = "/tmp/openclaims_uploads"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    gcp_cloud_sql_connection_name: Optional[str] = None
    
    app_name: str = "OpenClaims API"
    debug: bool = False
    cors_allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins from environment."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
