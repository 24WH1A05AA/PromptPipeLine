"""
Stage 1: Bug Understanding Module
Uses Role Prompting + Structured Output to analyze and classify bugs
"""

import json
from typing import Any, Dict, List, Optional

from llm import call_llm, LLMError
from prompts import STAGE_1_SYSTEM_PROMPT, STAGE_1_TEMPLATE, PromptTemplate


# ── Required fields that must be present in the LLM response ──

REQUIRED_FIELDS = [
    "title",
    "description",
    "error_type",
    "affected_module",
    "environment",
    "steps_to_reproduce",
    "stack_trace_summary",
]

FIELD_TYPES = {
    "title": str,
    "description": str,
    "error_type": str,
    "affected_module": str,
    "environment": str,
    "steps_to_reproduce": list,
    "stack_trace_summary": str,
}


class Stage1ValidationError(Exception):
    """Raised when Stage 1 output fails validation."""
    pass


def build_prompt(
    bug_report: str,
    stack_trace: str,
    environment: str,
) -> str:
    """
    Build the Stage 1 prompt by filling the template with user input.

    Parameters
    ----------
    bug_report : str
        The raw bug description.
    stack_trace : str
        The full stack trace text.
    environment : str
        Environment/context information.

    Returns
    -------
    str
        The filled prompt ready to send to the LLM.
    """
    template = PromptTemplate(STAGE_1_TEMPLATE, name="Stage 1 - Bug Analysis")
    return template.fill({
        "bug_report": bug_report,
        "stack_trace": stack_trace,
        "environment": environment,
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
    Stage1ValidationError
        If the response is not valid JSON.
    """
    # Strip any whitespace, code fences, or extra text
    cleaned = raw_response.strip()

    # Remove markdown code fences if present
    if cleaned.startswith("```"):
        # Find the first and last ```
        lines = cleaned.split("\n")
        # Remove first line (```json or ```)
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise Stage1ValidationError(
            f"Failed to parse LLM response as JSON: {e}\n\n"
            f"Raw response received:\n{raw_response}"
        )

    if not isinstance(parsed, dict):
        raise Stage1ValidationError(
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
        The validated dictionary (may include defaults for missing optional fields).

    Raises
    ------
    Stage1ValidationError
        If required fields are missing or have incorrect types.
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
            actual_value = parsed[field]
            if expected_type == list:
                if not isinstance(actual_value, list):
                    errors.append(
                        f"Field '{field}' should be a list, got {type(actual_value).__name__}"
                    )
            elif expected_type == str:
                if not isinstance(actual_value, str):
                    errors.append(
                        f"Field '{field}' should be a string, got {type(actual_value).__name__}"
                    )

    # Validate steps_to_reproduce contains strings
    if "steps_to_reproduce" in parsed and isinstance(parsed["steps_to_reproduce"], list):
        for i, step in enumerate(parsed["steps_to_reproduce"]):
            if not isinstance(step, str):
                errors.append(
                    f"steps_to_reproduce[{i}] should be a string, got {type(step).__name__}"
                )

    if errors:
        raise Stage1ValidationError(
            "Stage 1 output validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return parsed


def stage1_understand(
    bug_report: str,
    stack_trace: str,
    environment: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute Stage 1: Understand the bug.

    This function:
    1. Builds the prompt from the bug report, stack trace, and environment
    2. Calls the LLM with role prompting for structured JSON output
    3. Parses the JSON response
    4. Validates all required fields
    5. Returns the structured dictionary

    Parameters
    ----------
    bug_report : str
        The raw bug description from the user.
    stack_trace : str
        The full stack trace text.
    environment : str
        Environment/context information.
    model : str, optional
        The model identifier to use. Falls back to MODEL env var.
    api_key : str, optional
        OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.

    Returns
    -------
    Dict[str, Any]
        A validated dictionary with the following keys:
        - title: str
        - description: str
        - error_type: str
        - affected_module: str
        - environment: str
        - steps_to_reproduce: List[str]
        - stack_trace_summary: str

    Raises
    ------
    Stage1ValidationError
        If the LLM response cannot be parsed or validated.
    LLMError
        If the LLM call fails (auth, rate limit, timeout, network, etc.).
    """
    # Step 1: Build the prompt
    prompt = build_prompt(bug_report, stack_trace, environment)

    # Step 2: Call the LLM
    raw_response = call_llm(
        prompt=prompt,
        system_prompt=STAGE_1_SYSTEM_PROMPT,
        model=model,
        api_key=api_key,
        temperature=0.1,  # Low temperature for consistent structured output
        max_tokens=1024,
    )

    # Step 3: Parse the JSON response
    parsed = parse_llm_response(raw_response)

    # Step 4: Validate required fields
    validated = validate_fields(parsed)

    return validated