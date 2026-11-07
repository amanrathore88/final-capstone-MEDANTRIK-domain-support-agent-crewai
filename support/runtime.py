"""Runtime isolation, deterministic mock settings, and telemetry suppression."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def prepare_runtime() -> None:
    """Configure environment variables and storage shims before framework imports."""
    os.environ.update({
        "MOCK_LLM": "true",
        "CREWAI_DISABLE_TELEMETRY": "true",
        "OTEL_SDK_DISABLED": "true",
        "CREWAI_TRACING_ENABLED": "false",
        "ANONYMIZED_TELEMETRY": "false",
        "HF_HUB_OFFLINE": "0",  # Allow initial download if needed
        "HF_HOME": str(Path.home() / ".cache" / "huggingface"),
        "CREWAI_STORAGE_DIR": str(ROOT / ".runtime" / "crewai"),
        "LANGCHAIN_TRACING_V2": "false",
        "LANGSMITH_TRACING": "false",
        "LANGSMITH_OTEL_ENABLED": "false",
    })

    # Ensure local secure directory exists for CrewAI credentials without touching AppData
    try:
        from crewai_core.token_manager import TokenManager

        def project_credentials_path() -> Path:
            path = ROOT / ".runtime" / "crewai" / "credentials"
            path.mkdir(parents=True, exist_ok=True)
            return path

        TokenManager._get_secure_storage_path = staticmethod(project_credentials_path)
    except Exception:
        pass


prepare_runtime()
