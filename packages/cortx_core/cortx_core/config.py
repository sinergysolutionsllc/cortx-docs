from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional


class Settings(BaseSettings):
    app_name: str = Field(default="cortx")
    env: str = Field(default="dev")
    log_level: str = Field(default="INFO")
    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@db:5432/cortx")
    jwt_public_key: Optional[str] = None
    jwt_audience: Optional[str] = None
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])
    default_tenant_id: str = Field(default="public")

    # CORTX Three-Mode Architecture Configuration
    cortx_validation_mode: str = Field(
        default="static", description="Default validation mode: static, hybrid, agentic"
    )
    registry_url: str = Field(
        default="http://localhost:8081", description="CORTX RulePack Registry URL"
    )

    # RAG/AI Configuration
    google_api_key: Optional[str] = Field(default=None, description="Google Gemini API key for RAG")
    rag_faiss_path: str = Field(
        default="/app/policy_vectors", description="Path to FAISS policy vector store"
    )
    rag_confidence_threshold: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Confidence threshold for agentic mode"
    )

    # Mode-specific settings
    enable_hybrid_comparison: bool = Field(
        default=True, description="Enable comparison dashboard in hybrid mode"
    )
    comparison_dashboard_url: str = Field(
        default="/analytics", description="URL for training dashboard"
    )

    # Reconciliation Configuration
    recon_threshold: float = Field(
        default=0.01, description="Material variance threshold for reconciliation"
    )

    class Config:
        env_file = ".env"
        env_prefix = "CORTX_"
        extra = "ignore"


settings = Settings()
