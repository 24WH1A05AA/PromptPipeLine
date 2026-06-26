"""
Stage 3: Fix Generation Module
Uses Goal-Oriented Prompting to generate a developer fix report
"""

import json
from typing import Any, Dict, List, Optional

from llm import call_llm, LLMError
from prompts import STAGE_3_SYSTEM_PROMPT, STAGE_3_TEMPLATE, PromptTemplate


# ── Required fields that must be present in the LLM response ──

REQUIRED_FIELDS = [
    "recommended_fix",
    "developer_notes",
    "testing_strategy",
    "final_report",
]

FIELD_TYPES = {
    "recommended_fix": str,
    "developer_notes": str,
    "testing_strategy": str,
    "final_report": str,
}


class Stage3ValidationError(Exception):
    """Raised when Stage 3 output fails validation."""
    pass


def build_prompt(stage_1_json: str, stage_2_json: str) -> str:
    """
    Build the Stage 3 prompt by filling the template with Stage 1 and Stage 2 output.

    Parameters
    ----------
    stage_1_json : str
        The JSON string from Stage 1 (Bug Understanding).
    stage_2_json : str
        The JSON string from Stage 2 (Root Cause Diagnosis).

    Returns
    -------
    str
        The filled prompt ready to send to the LLM.
    """
    template = PromptTemplate(STAGE_3_TEMPLATE, name="Stage 3 - Fix Generation")
    return template.fill({
        "stage_1_json": stage_1_json,
        "stage_2_json": stage_2_json,
    })


def parse_llm_response(raw_response: str) -> Dict[str, Any]:
    """
    Parse the raw LLM response string into a dictionary.

    Parameters
    ----------
    raw_response : str
        The raw text returned by the LLM.

    Returns
    -------
    Dict[str, Any]
        Parsed JSON dictionary.

    Raises
    ------
    Stage3ValidationError
        If the response is not valid JSON.
    """
    cleaned = raw_response.strip()

    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise Stage3ValidationError(
            f"Failed to parse LLM response as JSON: {e}\n\n"
            f"Raw response received:\n{raw_response}"
        )

    if not isinstance(parsed, dict):
        raise Stage3ValidationError(
            f"Expected a JSON object (dict), but got {type(parsed).__name__}. "
            f"Response: {raw_response}"
        )

    return parsed


def validate_fields(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that all required fields are present and of the correct type.

    Parameters
    ----------
    parsed : Dict[str, Any]
        The parsed JSON dictionary from the LLM.

    Returns
    -------
    Dict[str, Any]
        The validated dictionary.

    Raises
    ------
    Stage3ValidationError
        If required fields are missing or have incorrect types.
    """
    errors: List[str] = []

    for field in REQUIRED_FIELDS:
        if field not in parsed:
            errors.append(f"Missing required field: '{field}'")
        elif parsed[field] is None:
            errors.append(f"Field '{field}' is null/empty")

    for field, expected_type in FIELD_TYPES.items():
        if field in parsed and parsed[field] is not None:
            if not isinstance(parsed[field], expected_type):
                errors.append(
                    f"Field '{field}' should be a {expected_type.__name__}, "
                    f"got {type(parsed[field]).__name__}"
                )

    if errors:
        raise Stage3ValidationError(
            "Stage 3 output validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return parsed


def stage3_fix(
    stage_1_json: str,
    stage_2_json: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute Stage 3: Generate a fix report using Goal-Oriented Prompting.

    Takes Stage 1 and Stage 2 JSON outputs, calls the LLM with goal-oriented
    prompting to produce a developer-ready fix report, parses and validates
    the response, and returns the structured dictionary.

    Parameters
    ----------
    stage_1_json : str
        The JSON string from Stage 1 (Bug Understanding).
    stage_2_json : str
        The JSON string from Stage 2 (Root Cause Diagnosis).
    model : str, optional
        The model identifier to use. Falls back to MODEL env var.
    api_key : str, optional
        OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.

    Returns
    -------
    Dict[str, Any]
        A validated dictionary with the following keys:
        - recommended_fix: str
        - developer_notes: str
        - testing_strategy: str
        - final_report: str

    Raises
    ------
    Stage3ValidationError
        If the LLM response cannot be parsed or validated.
    LLMError
        If the LLM call fails.
    """
    prompt = build_prompt(stage_1_json, stage_2_json)

    raw_response = call_llm(
        prompt=prompt,
        system_prompt=STAGE_3_SYSTEM_PROMPT,
        model=model,
        api_key=api_key,
        temperature=0.3,
        max_tokens=1536,
    )

    parsed = parse_llm_response(raw_response)
    validated = validate_fields(parsed)

    return validated