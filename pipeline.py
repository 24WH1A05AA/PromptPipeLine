"""
Pipeline Orchestration Module
Manages prompt transformation chains and execution flow
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from llm import call_llm, LLMError
from prompts import PromptTemplate
from parser import PromptParser
from utils import load_pipeline_config, save_pipeline_config
from stage1 import stage1_understand, Stage1ValidationError
from stage2 import stage2_analyze, Stage2ValidationError
from stage3 import stage3_fix, Stage3ValidationError
from presets import (
    get_preset,
    get_input_fields,
    get_stage_prompts,
    list_presets,
)

logger = logging.getLogger(__name__)


# ── Top-level orchestrator (original bug-triage pipeline) ──


def run_pipeline(
    bug_report: str,
    stack_trace: str = "",
    environment: str = "",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full 3-stage bug analysis pipeline (original)."""
    if not bug_report or not bug_report.strip():
        raise ValueError("bug_report must not be empty.")

    pipeline_start = time.time()

    t0 = time.time()
    try:
        stage1_result = stage1_understand(
            bug_report=bug_report, stack_trace=stack_trace,
            environment=environment, model=model, api_key=api_key,
        )
    except (Stage1ValidationError, LLMError) as e:
        logger.error("[Stage 1] Failed: %s", e)
        raise
    logger.info("[Stage 1] Completed in %.2fs", time.time() - t0)

    t0 = time.time()
    try:
        stage2_result = stage2_analyze(
            stage_1_json=json.dumps(stage1_result),
            model=model, api_key=api_key,
        )
    except (Stage2ValidationError, LLMError) as e:
        logger.error("[Stage 2] Failed: %s", e)
        raise
    logger.info("[Stage 2] Completed in %.2fs", time.time() - t0)

    t0 = time.time()
    try:
        stage3_result = stage3_fix(
            stage_1_json=json.dumps(stage1_result),
            stage_2_json=json.dumps(stage2_result),
            model=model, api_key=api_key,
        )
    except (Stage3ValidationError, LLMError) as e:
        logger.error("[Stage 3] Failed: %s", e)
        raise
    logger.info("[Stage 3] Completed in %.2fs", time.time() - t0)

    total_time = round(time.time() - pipeline_start, 2)
    return {"stage1": stage1_result, "stage2": stage2_result,
            "stage3": stage3_result, "execution_time": total_time}


# ── Generic preset-based runner ──


def run_preset_pipeline(
    preset_key: str,
    field_values: Dict[str, str],
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run a 3-stage pipeline defined by a preset.

    Each stage dynamically loads its system prompt and template from the
    preset config, fills the template with field values, calls the LLM,
    and passes the result to the next stage.

    Parameters
    ----------
    preset_key : str
        Key of a registered preset (e.g. "bug_triage", "support_ticket").
    field_values : Dict[str, str]
        Mapping of input field keys (e.g. "field_1", "field_2") to their text.
    model : str, optional
        LLM model identifier.
    api_key : str, optional
        OpenRouter API key.

    Returns
    -------
    Dict[str, Any]
        {"stage1": ..., "stage2": ..., "stage3": ..., "execution_time": float}

    Raises
    ------
    ValueError
        If preset_key is unknown.
    LLMError
        If any LLM call fails.
    """
    pipeline_start = time.time()

    # Build base fill variables from field values + raw_ variants
    _base_fill: Dict[str, str] = {}
    for fk, fv in field_values.items():
        _base_fill[fk] = fv
        _base_fill[f"raw_{fk}"] = fv

    def _run_stage(
        stage_num: int,
        stage1_json: str = "",
        stage2_json: str = "",
    ) -> Dict[str, Any]:
        prompts = get_stage_prompts(preset_key, stage_num)
        template = PromptTemplate(prompts["template"],
                                  name=f"{preset_key}_stage{stage_num}")

        fill_vars: Dict[str, str] = dict(_base_fill)
        if stage1_json:
            fill_vars["stage1_json"] = stage1_json
        if stage2_json:
            fill_vars["stage2_json"] = stage2_json

        filled = template.fill(fill_vars)
        raw = call_llm(
            prompt=filled,
            system_prompt=prompts["system"],
            model=model, api_key=api_key,
            temperature=0.2,
            max_tokens=2048,
        )

        try:
            return json.loads(raw) if raw.strip().startswith(("{", "[")) else {"raw": raw}
        except json.JSONDecodeError:
            return {"raw": raw}

    # Stage 1
    logger.info("[%s] Stage 1: starting", preset_key)
    t0 = time.time()
    stage1 = _run_stage(1)
    logger.info("[%s] Stage 1: done in %.2fs", preset_key, time.time() - t0)
    s1_json = json.dumps(stage1)

    # Stage 2
    logger.info("[%s] Stage 2: starting", preset_key)
    t0 = time.time()
    stage2 = _run_stage(2, stage1_json=s1_json)
    logger.info("[%s] Stage 2: done in %.2fs", preset_key, time.time() - t0)
    s2_json = json.dumps(stage2)

    # Stage 3
    logger.info("[%s] Stage 3: starting", preset_key)
    t0 = time.time()
    stage3 = _run_stage(3, stage1_json=s1_json, stage2_json=s2_json)
    logger.info("[%s] Stage 3: done in %.2fs", preset_key, time.time() - t0)

    total = round(time.time() - pipeline_start, 2)
    return {"stage1": stage1, "stage2": stage2, "stage3": stage3,
            "execution_time": total}


# ── Class-based pipeline (kept for reuse / future extension) ──


class PipelineStep:
    """Represents a single step in the prompt pipeline."""

    def __init__(
        self,
        name: str,
        template: PromptTemplate,
        system_prompt: Optional[str] = None,
        parser: Optional[PromptParser] = None,
    ):
        self.name = name
        self.template = template
        self.system_prompt = system_prompt
        self.parser = parser
        self.output: Optional[str] = None

    def execute(
        self,
        llm_client,
        input_data: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> str:
        prompt = self.template.fill({"input": input_data})
        self.output = call_llm(
            prompt=prompt,
            system_prompt=self.system_prompt,
            model=model,
            api_key=api_key,
            temperature=0.1,
            max_tokens=1024,
        )
        return self.output


class Pipeline:
    """Orchestrates a sequence of prompt transformation steps."""

    def __init__(self, name: str = "Untitled Pipeline"):
        self.name = name
        self.steps: List[PipelineStep] = []

    def add_step(self, step: PipelineStep) -> None:
        self.steps.append(step)

    def remove_step(self, index: int) -> None:
        if 0 <= index < len(self.steps):
            self.steps.pop(index)

    def reorder_steps(self, new_order: List[int]) -> None:
        self.steps = [self.steps[i] for i in new_order if 0 <= i < len(self.steps)]

    def execute(
        self,
        llm_client,
        initial_input: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> List[str]:
        outputs = []
        current_input = initial_input
        for step in self.steps:
            output = step.execute(llm_client, current_input, model=model, api_key=api_key)
            outputs.append(output)
            current_input = output
        return outputs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "steps": [
                {
                    "name": step.name,
                    "template": step.template.to_dict(),
                    "system_prompt": step.system_prompt,
                }
                for step in self.steps
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pipeline":
        pipeline = cls(name=data.get("name", "Untitled Pipeline"))
        for step_data in data.get("steps", []):
            template = PromptTemplate.from_dict(step_data["template"])
            step = PipelineStep(
                name=step_data["name"],
                template=template,
                system_prompt=step_data.get("system_prompt"),
            )
            pipeline.add_step(step)
        return pipeline

    def export_to_json(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def import_from_json(cls, filepath: str) -> "Pipeline":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


class PipelineManager:
    """Manages multiple pipelines, including saving, loading, and history."""

    def __init__(self, storage_path: str = "pipelines.json"):
        self.storage_path = storage_path
        self.pipelines: Dict[str, Pipeline] = {}

    def save_pipeline(self, pipeline: Pipeline) -> None:
        self.pipelines[pipeline.name] = pipeline
        data = {name: p.to_dict() for name, p in self.pipelines.items()}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_pipeline(self, name: str) -> Optional[Pipeline]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if name in data:
                pipeline = Pipeline.from_dict(data[name])
                self.pipelines[name] = pipeline
                return pipeline
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return None

    def list_pipelines(self) -> List[str]:
        return list(self.pipelines.keys())

    def delete_pipeline(self, name: str) -> None:
        self.pipelines.pop(name, None)
