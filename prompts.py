"""
Prompt Templates Module
Defines prompt templates, variable injection, and chaining logic
"""

import re
from typing import Any, Dict, List, Optional


# ── Stage 1: Bug Analysis (Role Prompting + Structured Output) ──

STAGE_1_SYSTEM_PROMPT = """You are a Senior Software Debugging Engineer. Your only job is to analyze bug reports and stack traces to produce a structured, actionable summary of the issue.

Rules:
- Return ONLY valid JSON.
- Do NOT wrap the JSON in markdown code blocks or any other formatting.
- Do NOT include any text before or after the JSON.
- Do NOT explain your reasoning.
- Use the exact schema provided."""

STAGE_1_TEMPLATE = """Analyze the following bug report and produce a structured JSON summary.

Bug Report:
{{bug_report}}

Stack Trace:
{{stack_trace}}

Environment:
{{environment}}

Return ONLY valid JSON using this exact schema (no markdown, no explanations):
{
    "title": "Short descriptive title of the bug",
    "description": "Clear description of what the bug is",
    "error_type": "The type of error (e.g., ValueError, TypeError, UnicodeEncodeError)",
    "affected_module": "The module or file where the bug occurs",
    "environment": "Relevant environment details",
    "steps_to_reproduce": ["Step 1", "Step 2", "Step 3"],
    "stack_trace_summary": "Summary of the most important part of the stack trace"
}"""


# ── Stage 2: Root Cause Diagnosis (Chain-of-Thought) ──

STAGE_2_SYSTEM_PROMPT = """You are a Senior Software Debugging Engineer performing root cause analysis using Chain-of-Thought reasoning.

For every bug you analyze, walk through your reasoning step by step internally, then produce a structured JSON diagnosis.

Rules:
- Return ONLY valid JSON.
- Do NOT wrap the JSON in markdown code blocks or any other formatting.
- Do NOT include any text before or after the JSON.
- Do NOT explain your reasoning in the output — put your reasoning inside the "reasoning" field.
- Use the exact schema provided."""

STAGE_2_TEMPLATE = """Using Chain-of-Thought reasoning, analyze this bug to determine its severity, priority, root cause, and confidence level.

Stage 1 Analysis (Bug Understanding):
{{stage_1_json}}

Work through the following reasoning chain:
1. What type of error is this? How severe is the impact?
2. Does this block critical functionality or is it a minor issue?
3. Based on the stack trace and environment, what is the most likely root cause?
4. How confident are you in this diagnosis given the available information?
5. Summarize your step-by-step reasoning.

Return ONLY valid JSON using this exact schema (no markdown, no explanations):
{
    "severity": "critical / high / medium / low",
    "priority": "urgent / high / medium / low",
    "root_cause": "Concise description of the root cause",
    "confidence": "high / medium / low",
    "reasoning": "Step-by-step chain-of-thought reasoning that led to this diagnosis"
}"""


# ── Stage 3: Fix Generation (Goal-Oriented Prompting) ──

STAGE_3_SYSTEM_PROMPT = """You are a Senior Software Engineer writing a professional bug fix report. Your goal is to produce a concise, actionable fix document that a developer can use immediately.

Focus on:
- A clear, correct fix with code examples
- Practical developer notes covering pitfalls and edge cases
- A concrete testing strategy with specific test cases
- A professional final report summarizing the entire analysis

Rules:
- Return ONLY valid JSON.
- Do NOT wrap the JSON in markdown code blocks or any other formatting.
- Do NOT include any text before or after the JSON.
- Use the exact schema provided."""

STAGE_3_TEMPLATE = """Generate a professional bug fix report based on the following analysis.

Stage 1 Analysis (Bug Understanding):
{{stage_1_json}}

Stage 2 Analysis (Root Cause Diagnosis):
{{stage_2_json}}

Your goal is to produce a complete developer-facing fix document.

Return ONLY valid JSON using this exact schema (no markdown, no explanations):
{
    "recommended_fix": "Clear, correct fix with code example. Show before/after.",
    "developer_notes": "Key implementation notes, edge cases, and pitfalls to avoid",
    "testing_strategy": "Specific test cases and testing approach to verify the fix",
    "final_report": "Professional one-paragraph summary covering the bug, root cause, fix, and impact"
}"""


class PromptTemplate:
    """Represents a prompt template with variables that can be filled dynamically."""

    def __init__(self, template: str, name: str = "Untitled Template"):
        """Initialize a prompt template with a template string and name."""
        self.template = template
        self.name = name
        self.variables: List[str] = self._extract_variables()

    def _extract_variables(self) -> List[str]:
        """Extract variable placeholders (e.g., {{var_name}}) from the template."""
        return re.findall(r"\{\{(\w+)\}\}", self.template)

    def fill(self, variables: Dict[str, str]) -> str:
        """Replace placeholders in the template with provided variable values."""
        result = self.template
        for var_name, value in variables.items():
            result = result.replace("{{" + var_name + "}}", value)
        return result

    def validate(self, variables: Dict[str, str]) -> bool:
        """Check if all required variables are provided."""
        return len(self.get_missing_variables(variables)) == 0

    def get_missing_variables(self, variables: Dict[str, str]) -> List[str]:
        """Return a list of required variables that are missing from the input."""
        return [v for v in self.variables if v not in variables or not variables[v]]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the template to a dictionary."""
        return {
            "name": self.name,
            "template": self.template,
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """Deserialize a template from a dictionary."""
        return cls(template=data["template"], name=data.get("name", "Untitled Template"))


class PromptLibrary:
    """Manages a collection of reusable prompt templates."""

    def __init__(self):
        """Initialize an empty prompt library."""
        self.templates: Dict[str, PromptTemplate] = {}

    def add_template(self, name: str, template: PromptTemplate) -> None:
        """Add a named template to the library."""
        self.templates[name] = template

    def remove_template(self, name: str) -> None:
        """Remove a template from the library by name."""
        self.templates.pop(name, None)

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Retrieve a template by name."""
        return self.templates.get(name)

    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self.templates.keys())

    def export_to_json(self, filepath: str) -> None:
        """Export the template library to a JSON file."""
        import json
        data = {
            name: template.to_dict()
            for name, template in self.templates.items()
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def import_from_json(cls, filepath: str) -> "PromptLibrary":
        """Import a template library from a JSON file."""
        import json
        library = cls()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for name, template_data in data.items():
            library.add_template(name, PromptTemplate.from_dict(template_data))
        return library


class SystemPrompt:
    """Represents a system-level prompt for setting LLM behavior."""

    def __init__(self, content: str, role: str = "assistant"):
        """Initialize a system prompt with content and an optional role."""
        self.content = content
        self.role = role

    def to_dict(self) -> Dict[str, str]:
        """Serialize the system prompt to a dictionary."""
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "SystemPrompt":
        """Deserialize a system prompt from a dictionary."""
        return cls(content=data["content"], role=data.get("role", "assistant"))