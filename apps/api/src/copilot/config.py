from functools import lru_cache

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("apps/api/.env", ".env"),
        env_prefix="",
        extra="ignore",
    )

    app_env: str = "local"
    app_cors_origins: list[str] = ["http://localhost:3000"]
    clinical_trials_base_url: AnyHttpUrl = AnyHttpUrl(
        "https://clinicaltrials.gov/api/v2"
    )
    clinical_trials_fallback_base_url: AnyHttpUrl | None = AnyHttpUrl(
        "https://oncology-trial-assistant-web.vercel.app/api/clinical-trials"
    )
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_publishable_key: str = ""
    supabase_service_role_key: str = ""
    auth_disabled: bool = True
    demo_access_enabled: bool = False
    demo_user_id: str = "00000000-0000-0000-0000-000000000001"
    upstream_timeout_seconds: float = 10.0
    upstream_max_attempts: int = 3
    ncbi_base_url: AnyHttpUrl = AnyHttpUrl(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    )
    ncbi_api_key: str = ""
    ncbi_tool: str = "oncology_trial_feasibility_copilot"
    ncbi_email: str = ""
    groq_api_key: str = ""
    groq_model: str = ""
    groq_fallback_model: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
