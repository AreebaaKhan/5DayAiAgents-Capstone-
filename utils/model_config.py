"""Model selection helpers for the content pipeline."""

import os


DEFAULT_MODEL = "gemini-2.5-flash"


def get_model_name() -> str:
    """Return the configured model name, falling back to the default."""
    return os.environ.get("CONTENT_PIPELINE_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL