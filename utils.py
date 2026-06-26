"""Utility functions — file I/O, config, formatting, and validation helpers."""

import json
import os
import re
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional


# ── JSON I/O ──

def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    """Load and parse a JSON file. Returns None if not found or malformed."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_json(filepath: str, data: Dict[str, Any]) -> bool:
    """Save a dictionary to a JSON file with 2-space indentation. Returns True on success."""
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


# ── Pipeline config (thin wrappers kept for backward compat) ──

def load_pipeline_config(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a pipeline configuration from a JSON file."""
    return load_json(filepath)


def save_pipeline_config(filepath: str, config: Dict[str, Any]) -> bool:
    """Save a pipeline configuration to a JSON file."""
    return save_json(filepath, config)


# ── Environment ──

def load_environment_variables(env_file: str = ".env") -> Dict[str, str]:
    """
    Parse a .env file and return key-value pairs as a dict.
    Skips blank lines and comments (#). Does NOT call os.environ.
    """
    result: Dict[str, str] = {}
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return result


def validate_api_key(api_key: str) -> bool:
    """Return True if api_key is a non-empty string with at least 20 characters."""
    return isinstance(api_key, str) and len(api_key.strip()) >= 20


# ── Text helpers ──

def sanitize_filename(filename: str) -> str:
    """Replace characters that are invalid in filenames with underscores."""
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
    return sanitized.strip(". ") or "file"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max_length, appending suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_timestamp(timestamp: Optional[float] = None) -> str:
    """Format a Unix timestamp (or now) as 'YYYY-MM-DD HH:MM:SS'."""
    dt = datetime.fromtimestamp(timestamp) if timestamp is not None else datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ── Cost estimation ──

# Prices per 1 000 tokens — (input_$/1k, output_$/1k)
_PRICING: Dict[str, tuple[float, float]] = {
    "openai/gpt-4o":               (0.005,  0.015),
    "openai/gpt-4o-mini":          (0.00015, 0.0006),
    "openai/gpt-3.5-turbo":        (0.0005, 0.0015),
    "anthropic/claude-3-haiku":    (0.00025, 0.00125),
    "anthropic/claude-3-sonnet":   (0.003,  0.015),
    "anthropic/claude-3-opus":     (0.015,  0.075),
    "google/gemini-pro":           (0.0005, 0.0015),
    "mistralai/mistral-large":     (0.004,  0.012),
}


def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """
    Estimate USD cost for an API call given token counts and model name.
    Returns 0.0 for unknown models.
    """
    rates = _PRICING.get(model)
    if not rates:
        return 0.0
    cost = (prompt_tokens / 1000) * rates[0] + (completion_tokens / 1000) * rates[1]
    return round(cost, 6)


# ── File helpers ──

def create_backup(filepath: str) -> Optional[str]:
    """
    Copy filepath to <filepath>.<timestamp>.bak.
    Returns the backup path, or None if the source does not exist.
    """
    if not os.path.isfile(filepath):
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.{ts}.bak"
    shutil.copy2(filepath, backup_path)
    return backup_path


def list_json_files(directory: str) -> List[str]:
    """Return sorted list of absolute paths to all *.json files in directory."""
    if not os.path.isdir(directory):
        return []
    return sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".json")
    )
