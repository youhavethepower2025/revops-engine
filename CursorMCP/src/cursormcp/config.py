"""Configuration management for CursorMCP"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with validation"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # Map env vars: CLOUDFLARE_API_TOKEN -> cloudflare_api_token
        env_prefix="",
    )
    
    # Cloudflare Configuration
    # These will read from CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID env vars
    CLOUDFLARE_API_TOKEN: Optional[str] = Field(
        default=None,
        description="Cloudflare API token"
    )
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = Field(
        default=None,
        description="Cloudflare account ID"
    )
    
    # Workspace Configuration
    WORKSPACE_ROOT: Path = Field(
        default_factory=lambda: Path.cwd(),
        description="Root directory for file operations"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # MCP Server Info
    MCP_SERVER_NAME: str = Field(default="cursormcp", description="MCP server name")
    MCP_SERVER_VERSION: str = Field(default="0.1.0", description="MCP server version")
    
    @property
    def cloudflare_api_token(self) -> Optional[str]:
        """Get Cloudflare API token"""
        return self.CLOUDFLARE_API_TOKEN
    
    @property
    def cloudflare_account_id(self) -> Optional[str]:
        """Get Cloudflare account ID"""
        return self.CLOUDFLARE_ACCOUNT_ID
    
    @property
    def workspace_root(self) -> Path:
        """Get workspace root"""
        return self.WORKSPACE_ROOT
    
    @property
    def log_level(self) -> str:
        """Get log level"""
        return self.LOG_LEVEL
    
    @property
    def mcp_server_name(self) -> str:
        """Get MCP server name"""
        return self.MCP_SERVER_NAME
    
    @property
    def mcp_server_version(self) -> str:
        """Get MCP server version"""
        return self.MCP_SERVER_VERSION
    
    @field_validator("WORKSPACE_ROOT", mode="before")
    @classmethod
    def validate_workspace_root(cls, v):
        """Convert string to Path and expand user"""
        if v is None:
            return Path.cwd()
        if isinstance(v, str):
            v = Path(v).expanduser().resolve()
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v:
            v = v.upper()
            if v not in valid_levels:
                raise ValueError(f"Log level must be one of {valid_levels}")
        return v or "INFO"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

