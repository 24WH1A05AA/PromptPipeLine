"""
Output Parser Module
Parses and transforms LLM output into structured data
"""

import json
import re
from typing import Any, Dict, List, Optional


class ParseError(Exception):
    """Raised when JSON parsing fails after all retry attempts."""
    pass


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from a string."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def parse_json(
    raw: str,
    call_llm_fn=None,
    max_attempts: int = 3,
) -> Dict[str, Any]:
    """
    Parse a JSON string from raw LLM output, retrying up to max_attempts times.

    On each failed attempt, call_llm_fn is invoked with a correction prompt
    asking the model to return only valid JSON. If call_llm_fn is None, the
    function retries only on the original text (useful for testing).

    Parameters
    ----------
    raw : str
        Raw text to parse.
    call_llm_fn : callable, optional
        A zero-argument callable that accepts (prompt: str) -> str.
        Signature: call_llm_fn(prompt) -> str
    max_attempts : int
        Maximum parse attempts (default 3).

    Returns
    -------
    Dict[str, Any]
        Parsed JSON object.

    Raises
    ------
    ParseError
        If all attempts fail.
    """
    current = raw
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return json.loads(_strip_fences(current))
        except json.JSONDecodeError as e:
            last_error = e
            if attempt < max_attempts and call_llm_fn is not None:
                retry_prompt = (
                    f"The previous response was invalid JSON.\n"
                    f"Error: {e}\n"
                    f"Return ONLY valid JSON."
                )
                current = call_llm_fn(retry_prompt)

    raise ParseError(
        f"Failed to parse valid JSON after {max_attempts} attempts. "
        f"Last error: {last_error}"
    )


# ── Supporting classes (used by pipeline infrastructure) ──


class PromptParser:
    """Base class for parsing LLM output into structured formats."""

    def __init__(self, name: str = "Untitled Parser"):
        self.name = name

    def parse(self, raw_output: str) -> Any:
        raise NotImplementedError

    def validate(self, parsed_output: Any) -> bool:
        raise NotImplementedError


class JSONParser(PromptParser):
    """Parses LLM output as JSON."""

    def __init__(self, strict: bool = True):
        super().__init__(name="JSON Parser")
        self.strict = strict

    def parse(self, raw_output: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from raw LLM output."""
        cleaned = _strip_fences(raw_output)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try extracting a JSON object/array substring
            match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
        return None

    def validate(self, parsed_output: Any) -> bool:
        return isinstance(parsed_output, (dict, list))


class MarkdownParser(PromptParser):
    """Parses LLM output into structured markdown sections."""

    def __init__(self):
        super().__init__(name="Markdown Parser")

    def parse(self, raw_output: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        current_heading = "__root__"
        lines: List[str] = []
        for line in raw_output.splitlines():
            if line.startswith("#"):
                if lines:
                    sections[current_heading] = "\n".join(lines).strip()
                current_heading = line.lstrip("#").strip()
                lines = []
            else:
                lines.append(line)
        if lines:
            sections[current_heading] = "\n".join(lines).strip()
        return sections

    def extract_code_blocks(self, raw_output: str) -> List[Dict[str, str]]:
        pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
        return [
            {"language": m.group(1) or "text", "code": m.group(2).strip()}
            for m in pattern.finditer(raw_output)
        ]

    def validate(self, parsed_output: Any) -> bool:
        return isinstance(parsed_output, dict)


class ListParser(PromptParser):
    """Parses LLM output into a list of items."""

    def __init__(self, delimiter: str = "\n", strip_numbers: bool = True):
        super().__init__(name="List Parser")
        self.delimiter = delimiter
        self.strip_numbers = strip_numbers

    def parse(self, raw_output: str) -> List[str]:
        items = [i.strip() for i in raw_output.split(self.delimiter) if i.strip()]
        if self.strip_numbers:
            items = [self._strip_list_numbers(i) for i in items]
        return items

    def _strip_list_numbers(self, item: str) -> str:
        return re.sub(r"^\s*\d+[.)]\s*", "", item)

    def validate(self, parsed_output: Any) -> bool:
        return isinstance(parsed_output, list)


class ParserRegistry:
    """Registry of available parsers."""

    def __init__(self):
        self.parsers: Dict[str, PromptParser] = {
            "json": JSONParser(),
            "markdown": MarkdownParser(),
            "list": ListParser(),
        }

    def register(self, name: str, parser: PromptParser) -> None:
        self.parsers[name] = parser

    def get(self, name: str) -> Optional[PromptParser]:
        return self.parsers.get(name)

    def list_parsers(self) -> List[str]:
        return list(self.parsers.keys())
