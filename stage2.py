"""
Stage 2: Root Cause Diagnosis Module
Uses Chain-of-Thought reasoning to determine severity, priority, root cause, and confidence
"""

import json
from typing import Any, Dict, List, Optional

from llm import call_llm, LLMError
from prompts import STAGE_2_SYSTEM_PROMPT, STAGE_2_TEMPLATE, PromptTemplate


# ── Required fields that must be present in the LLM response ──

REQUIRED_FIELDS = [
    "severity",
    "priority",
    "root_cause",
    "confidence",
    "reasoning",
]

VALID_SEVERITY = {"critical", "high", "medium", "low"}
VALID_PRIORITY = {"urgent", "high", "medium", "low"}
VALID_CONFIDENCE = {"high", "medium", "low"}

FIELD_TYPES = {
    "severity": str,
    "priority": str,
    "root_cause": str,
    "confidence": str,
    "reasoning": str,
}


class Stage2ValidationError(Exception):
    """Raised when Stage 2 output fails validation."""
    pass


def build_prompt(stage_1_json: str) -> str:
    """
    Build the Stage 2 prompt by filling the template with Stage 1 output.

    Parameters
    ----------
    stage_1_json : str
        The JSON string output from Stage 1 (Bug Understanding).

    Returns
    -------
    str
        The filled prompt ready to send to the LLM.
    """
    template = PromptTemplate(STAGE_2_TEMPLATE, name="Stage 2 - Root Cause Diagnosis")
    return template.fill({"stage_1_json": stage_1_json})


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
    Stage2ValidationError
        If the response is not valid JSON.
    """
    cleaned = raw_response.strip()

    # Remove markdown code fences if present
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
        raise Stage2ValidationError(
            f"Failed to parse LLM response as JSON: {e}\n\n"
            f"Raw response received:\n{raw_response}"
        )

    if not isinstance(parsed, dict):
        raise Stage2ValidationError(
            f"Expected a JSON object (dict), but got {type(parsed).__name__}. "
            f"Response: {raw_response}"
        )

    return parsed


def validate_fields(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that all required fields are present, of the correct type,
    and contain valid enum values.

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
    Stage2ValidationError
        If required fields are missing, have incorrect types, or invalid values.
    """
    errors: List[str] = []

    # Check for missing fields
    for field in REQUIRED_FIELDS:
        if field not in parsed:
            errors.append(f"Missing required field: '{field}'")
        elif parsed[field] is None:
            errors.append(f"Field '{field}' is null/empty")

    # Check field types
    for field, expected_type in FIELD_TYPES.items():
        if field in parsed and parsed[field] is not None:
            if not isinstance(parsed[field], expected_type):
                errors.append(
                    f"Field '{field}' should be a {expected_type.__name__}, "
                    f"got {type(parsed[field]).__name__}"
                )

    # Validate enum values
    if "severity" in parsed and isinstance(parsed["severity"], str):
        val = parsed["severity"].lower()
        if val not in VALID_SEVERITY:
            errors.append(
                f"Field 'severity' must be one of {VALID_SEVERITY}, got '{parsed['severity']}'"
            )

    if "priority" in parsed and isinstance(parsed["priority"], str):
        val = parsed["priority"].lower()
        if val not in VALID_PRIORITY:
            errors.append(
                f"Field 'priority' must be one of {VALID_PRIORITY}, got '{parsed['priority']}'"
            )

    if "confidence" in parsed and isinstance(parsed["confidence"], str):
        val = parsed["confidence"].lower()
        if val not in VALID_CONFIDENCE:
            errors.append(
                f"Field 'confidence' must be one of {VALID_CONFIDENCE}, got '{parsed['confidence']}'"
            )

    if errors:
        raise Stage2ValidationError(
            "Stage 2 output validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return parsed


def stage2_analyze(
    stage_1_json: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute Stage 2: Analyze the bug using Chain-of-Thought reasoning.

    Takes the Stage 1 JSON output, calls the LLM with Chain-of-Thought
    prompting, parses the JSON response, and returns the validated dictionary.

    This function does NOT modify Stage 1 data.

    Parameters
    ----------
    stage_1_json : str
        The JSON string output from Stage 1 (Bug Understanding).
    model : str, optional
        The model identifier to use. Falls back to MODEL env var.
    api_key : str, optional
        OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.

    Returns
    -------
    Dict[str, Any]
        A validated dictionary with the following keys:
        - severity: str (critical / high / medium / low)
        - priority: str (urgent / high / medium / low)
        - root_cause: str
        - confidence: str (high / medium / low)
        - reasoning: str (chain-of-thought reasoning)

    Raises
    ------
    Stage2ValidationError
        If the LLM response cannot be parsed or validated.
    LLMError
        If the LLM call fails (auth, rate limit, timeout, network, etc.).
    """
    # Step 1: Build the prompt
    prompt = build_prompt(stage_1_json)

    # Step 2: Call the LLM
    raw_response = call_llm(
        prompt=prompt,
        system_prompt=STAGE_2_SYSTEM_PROMPT,
        model=model,
        api_key=api_key,
        temperature=0.2,  # Slightly higher for reasoning diversity
        max_tokens=1024,
    )

    # Step 3: Parse the JSON response
    parsed = parse_llm_response(raw_response)

    # Step 4: Validate required fields and enum values
    validated = validate_fields(parsed)

    return validated


def stage2_diagnose(
    stage_1_json: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute Stage 2: Diagnose the root cause using Chain-of-Thought reasoning.

    Alias for stage2_analyze(). Provided for backward compatibility.

    This function:
    1. Builds the prompt from the Stage 1 JSON output
    2. Calls the LLM with Chain-of-Thought prompting
    3. Parses the JSON response
    4. Validates all required fields and enum values
    5. Returns the structured dictionary

    Parameters
    ----------
    stage_1_json : str
        The JSON string output from Stage 1 (Bug Understanding).
    model : str, optional
        The model identifier to use. Falls back to MODEL env var.
    api_key : str, optional
        OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.

    Returns
    -------
    Dict[str, Any]
        A validated dictionary with the following keys:
        - severity: str (critical / high / medium / low)
        - priority: str (urgent / high / medium / low)
        - root_cause: str
        - confidence: str (high / medium / low)
        - reasoning: str (chain-of-thought reasoning)

    Raises
    ------
    Stage2ValidationError
        If the LLM response cannot be parsed or validated.
    LLMError
        If the LLM call fails (auth, rate limit, timeout, network, etc.).
    """
    # Step 1: Build the prompt
    prompt = build_prompt(stage_1_json)

    # Step 2: Call the LLM
    raw_response = call_llm(
        prompt=prompt,
        system_prompt=STAGE_2_SYSTEM_PROMPT,
        model=model,
        api_key=api_key,
        temperature=0.2,  # Slightly higher for reasoning diversity
        max_tokens=1024,
    )

    # Step 3: Parse the JSON response
    parsed = parse_llm_response(raw_response)

    # Step 4: Validate required fields and enum values
    validated = validate_fields(parsed)

    return validated