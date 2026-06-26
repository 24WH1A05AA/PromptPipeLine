"""
Pipeline Presets Module
Defines reusable pipeline configurations for different use cases.

Each preset specifies:
  - Display name, description, and icon
  - Input fields (labels, placeholders, heights)
  - Stage 1, 2, 3 system prompts and templates
  - Output schemas and validation requirements
"""

from typing import Any, Dict, List


# ── Preset type ──

PresetConfig = Dict[str, Any]

# ── Registry ──

_PRESETS: Dict[str, PresetConfig] = {}


def register_preset(config: PresetConfig) -> None:
    """Register a preset by its key."""
    _PRESETS[config["key"]] = config


def get_preset(key: str) -> PresetConfig:
    """Get a preset configuration by key."""
    return _PRESETS[key]


def list_presets() -> List[Dict[str, str]]:
    """Return a summary list of all registered presets for the UI selector."""
    return [
        {
            "key": p["key"],
            "label": p["label"],
            "description": p["description"],
            "icon": p.get("icon", "📋"),
        }
        for p in _PRESETS.values()
    ]


def get_input_fields(key: str) -> List[Dict[str, Any]]:
    """Return the input field configs for a given preset."""
    return _PRESETS[key]["inputs"]


def get_stage_prompts(key: str, stage: int) -> Dict[str, str]:
    """Return {'system': ..., 'template': ...} for the given stage (1-3)."""
    return _PRESETS[key][f"stage{stage}"]


def get_stage_metadata(key: str) -> List[Dict[str, str]]:
    """Return stage titles and techniques for the UI."""
    p = _PRESETS[key]
    return [
        {"num": "1", "title": p["stage1_title"], "technique": p["stage1_technique"]},
        {"num": "2", "title": p["stage2_title"], "technique": p["stage2_technique"]},
        {"num": "3", "title": p["stage3_title"], "technique": p["stage3_technique"]},
    ]


# ═══════════════════════════════════════════════════════════════
# 1. Bug Report Triage  (original — enhanced)
# ═══════════════════════════════════════════════════════════════

register_preset({
    "key": "bug_triage",
    "label": "🐛 Bug Report Triage",
    "description": "Analyse a bug report + stack trace → structured report, root cause, severity, fix suggestion",
    "icon": "🐛",

    "inputs": [
        {"key": "field_1", "label": "Bug Report", "placeholder": "Describe the bug in detail...", "height": 110},
        {"key": "field_2", "label": "Stack Trace", "placeholder": "Paste the full stack trace here...", "height": 140},
        {"key": "field_3", "label": "Environment", "placeholder": "OS, Python version, relevant packages...", "height": 75},
    ],

    "stage1_title": "Understand & Extract",
    "stage1_technique": "Role Prompting + Structured Output",
    "stage1": {
        "system": (
            "You are a Senior Software Debugging Engineer. Your only job is to analyse bug "
            "reports and stack traces to produce a structured, actionable summary of the issue.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown code blocks.\n"
            "- Use the exact schema provided."
        ),
        "template": (
            "Analyse the following bug report and produce a structured JSON summary.\n\n"
            "Bug Report:\n{{field_1}}\n\nStack Trace:\n{{field_2}}\n\nEnvironment:\n{{field_3}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "title": "Short descriptive title",\n'
            '    "description": "Clear description of the bug",\n'
            '    "error_type": "e.g. ValueError, TypeError",\n'
            '    "affected_module": "Module or file where the bug occurs",\n'
            '    "environment": "Relevant env details",\n'
            '    "steps_to_reproduce": ["Step 1", "Step 2"],\n'
            '    "stack_trace_summary": "Summary of the key stack trace line"\n'
            "}"
        ),
    },

    "stage2_title": "Analyse & Reason",
    "stage2_technique": "Chain-of-Thought Reasoning",
    "stage2": {
        "system": (
            "You are a Senior Software Debugging Engineer performing root cause analysis "
            "using Chain-of-Thought reasoning. Walk through your reasoning step by step, "
            "then produce a structured JSON diagnosis.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown.\n"
            "- Use the exact schema provided."
        ),
        "template": (
            "Using Chain-of-Thought reasoning, analyse this bug to determine its severity, "
            "priority, root cause, and confidence level.\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "severity": "critical / high / medium / low",\n'
            '    "priority": "urgent / high / medium / low",\n'
            '    "root_cause": "Concise description of the root cause",\n'
            '    "confidence": "high / medium / low",\n'
            '    "reasoning": "Step-by-step chain-of-thought reasoning"\n'
            "}"
        ),
    },

    "stage3_title": "Generate Report",
    "stage3_technique": "Goal-Oriented Prompting",
    "stage3": {
        "system": (
            "You are a Senior Software Engineer writing a professional bug fix report. "
            "Produce a concise, actionable fix document.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown.\n"
            "- Use the exact schema provided."
        ),
        "template": (
            "Generate a professional bug fix report based on the following analysis.\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Stage 2 Analysis:\n{{stage2_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "recommended_fix": "Clear fix with before/after code example",\n'
            '    "developer_notes": "Implementation notes, edge cases, pitfalls",\n'
            '    "testing_strategy": "Specific test cases to verify the fix",\n'
            '    "final_report": "Professional summary covering bug, root cause, fix, impact"\n'
            "}"
        ),
    },
})


# ═══════════════════════════════════════════════════════════════
# 2. Support Ticket Triage
# ═══════════════════════════════════════════════════════════════

register_preset({
    "key": "support_ticket",
    "label": "🎫 Support Ticket Triage",
    "description": "Raw customer message → structured ticket (type · priority · sentiment) + drafted reply",
    "icon": "🎫",

    "inputs": [
        {"key": "field_1", "label": "Customer Message", "placeholder": "Paste the raw customer message or support email...", "height": 180},
        {"key": "field_2", "label": "Product / Service Context", "placeholder": "What product/service does this relate to? Any relevant account info...", "height": 80},
    ],

    "stage1_title": "Classify & Extract",
    "stage1_technique": "Role Prompting + Structured Output",
    "stage1": {
        "system": (
            "You are a Senior Customer Support Engineer. Analyse the customer message "
            "and extract a structured ticket summary.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown.\n"
            "- Use the exact schema provided."
        ),
        "template": (
            "Analyse the following customer message and extract a structured ticket summary.\n\n"
            "Customer Message:\n{{field_1}}\n\n"
            "Context:\n{{field_2}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "ticket_type": "bug / feature_request / billing / account / general",\n'
            '    "priority": "urgent / high / medium / low",\n'
            '    "sentiment": "frustrated / neutral / positive",\n'
            '    "summary": "One-sentence summary of the issue",\n'
            '    "key_points": ["Key point 1", "Key point 2"],\n'
            '    "requested_action": "What the customer is asking for"\n'
            "}"
        ),
    },

    "stage2_title": "Analyse & Prioritise",
    "stage2_technique": "Chain-of-Thought Reasoning",
    "stage2": {
        "system": (
            "You are a Senior Support Engineer prioritising tickets. Use Chain-of-Thought "
            "reasoning to determine business impact and suggested response tone.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown."
        ),
        "template": (
            "Analyse this support ticket to determine business impact, response "
            "strategy, and escalation needs.\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "business_impact": "How many users affected / revenue impact",\n'
            '    "response_tone": "empathetic / professional / urgent / reassuring",\n'
            '    "escalation_needed": true / false,\n'
            '    "escalation_reason": "Why escalation is or is not needed",\n'
            '    "reasoning": "Step-by-step chain-of-thought"\n'
            "}"
        ),
    },

    "stage3_title": "Draft Reply",
    "stage3_technique": "Goal-Oriented Prompting",
    "stage3": {
        "system": (
            "You are a Customer Support Agent. Draft a professional, empathetic reply "
            "to the customer based on the analysis.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown."
        ),
        "template": (
            "Draft a reply to the customer based on the analysis below.\n\n"
            "Customer Message:\n{{raw_field_1}}\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Stage 2 Analysis:\n{{stage2_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "reply_subject": "Email subject line",\n'
            '    "reply_body": "Full reply email body (professional, empathetic tone)",\n'
            '    "internal_notes": "Brief internal notes for the support team",\n'
            '    "next_steps": ["Step 1", "Step 2"]\n'
            "}"
        ),
    },
})


# ═══════════════════════════════════════════════════════════════
# 3. Essay Grader
# ═══════════════════════════════════════════════════════════════

register_preset({
    "key": "essay_grader",
    "label": "📝 Essay Grader",
    "description": "Short essay + rubric → per-criterion scores with justification + overall feedback note",
    "icon": "📝",

    "inputs": [
        {"key": "field_1", "label": "Student Essay", "placeholder": "Paste the student's essay here...", "height": 250},
        {"key": "field_2", "label": "Rubric / Grading Criteria", "placeholder": "Describe the rubric: criteria, point values, passing threshold...", "height": 120},
    ],

    "stage1_title": "Extract & Segment",
    "stage1_technique": "Role Prompting + Structured Output",
    "stage1": {
        "system": (
            "You are an experienced educator and essay grader. Analyse the essay and "
            "extract a structured overview.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown.\n"
            "- Use the exact schema provided."
        ),
        "template": (
            "Analyse the following student essay and extract a structured overview.\n\n"
            "Essay:\n{{field_1}}\n\n"
            "Rubric:\n{{field_2}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "essay_length": "Number of words / paragraphs",\n'
            '    "main_thesis": "The central argument or thesis of the essay",\n'
            '    "key_arguments": ["Argument 1", "Argument 2"],\n'
            '    "evidence_quality": "strong / adequate / weak",\n'
            '    "structure_assessment": "Well-structured / Somewhat organised / Disorganised"\n'
            "}"
        ),
    },

    "stage2_title": "Score & Justify",
    "stage2_technique": "Chain-of-Thought Reasoning",
    "stage2": {
        "system": (
            "You are an experienced educator grading an essay. Score each criterion with "
            "a clear justification using Chain-of-Thought reasoning.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown."
        ),
        "template": (
            "Score the essay against each rubric criterion. Provide justification for each score.\n\n"
            "Rubric:\n{{raw_field_2}}\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "criterion_scores": [\n'
            '        {"criterion": "Criterion 1", "score": 4, "max": 5, "justification": "Why this score"},\n'
            '        {"criterion": "Criterion 2", "score": 3, "max": 5, "justification": "Why this score"}\n'
            '    ],\n'
            '    "total_score": 7,\n'
            '    "max_total": 10,\n'
            '    "percentage": 70,\n'
            '    "passed": true,\n'
            '    "reasoning": "Step-by-step reasoning behind the scores"\n'
            "}"
        ),
    },

    "stage3_title": "Generate Feedback",
    "stage3_technique": "Goal-Oriented Prompting",
    "stage3": {
        "system": (
            "You are an experienced educator writing constructive feedback for a student. "
            "Be specific, encouraging, and actionable.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown."
        ),
        "template": (
            "Generate constructive feedback for the student based on the essay and grading analysis.\n\n"
            "Original Essay:\n{{raw_field_1}}\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Stage 2 Scores:\n{{stage2_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "overall_feedback": "Detailed overall feedback paragraph",\n'
            '    "strengths": ["Strength 1", "Strength 2"],\n'
            '    "areas_for_improvement": ["Area 1", "Area 2"],\n'
            '    "actionable_tips": ["Tip 1", "Tip 2"]\n'
            "}"
        ),
    },
})


# ═══════════════════════════════════════════════════════════════
# 4. Meeting Notes → Actions
# ═══════════════════════════════════════════════════════════════

register_preset({
    "key": "meeting_actions",
    "label": "📋 Meeting Notes → Actions",
    "description": "Messy meeting transcript → summary + owner-assigned action items + follow-up email",
    "icon": "📋",

    "inputs": [
        {"key": "field_1", "label": "Meeting Transcript / Notes", "placeholder": "Paste the raw meeting transcript, notes, or voice-to-text output...", "height": 250},
        {"key": "field_2", "label": "Attendees & Roles (optional)", "placeholder": "List of attendees and their roles, e.g. Alice (PM), Bob (Dev)...", "height": 80},
    ],

    "stage1_title": "Clean & Structure",
    "stage1_technique": "Role Prompting + Structured Output",
    "stage1": {
        "system": (
            "You are a skilled Executive Assistant. Clean up messy meeting notes and "
            "extract a structured summary.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown.\n"
            "- Use the exact schema provided."
        ),
        "template": (
            "Clean up and structure the following meeting notes.\n\n"
            "Transcript:\n{{field_1}}\n\n"
            "Attendees:\n{{field_2}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "meeting_summary": "Brief one-paragraph summary of what was discussed",\n'
            '    "key_discussion_points": ["Point 1", "Point 2", "Point 3"],\n'
            '    "decisions_made": ["Decision 1", "Decision 2"],\n'
            '    "unresolved_items": ["Item 1", "Item 2"]\n'
            "}"
        ),
    },

    "stage2_title": "Assign Ownership",
    "stage2_technique": "Chain-of-Thought Reasoning",
    "stage2": {
        "system": (
            "You are a Project Manager extracting action items from meeting notes. "
            "Assign clear owners and deadlines using Chain-of-Thought reasoning.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown."
        ),
        "template": (
            "Extract action items from the meeting and assign owners and deadlines.\n\n"
            "Attendees:\n{{raw_field_2}}\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "action_items": [\n'
            '        {"action": "What needs to be done", "owner": "Person", "deadline": "Date or timeframe", "priority": "high / medium / low"}\n'
            '    ],\n'
            '    "unassigned_items": ["Item needing owner"],\n'
            '    "next_meeting_agenda": ["Item 1", "Item 2"],\n'
            '    "reasoning": "Step-by-step reasoning"\n'
            "}"
        ),
    },

    "stage3_title": "Generate Follow-Up",
    "stage3_technique": "Goal-Oriented Prompting",
    "stage3": {
        "system": (
            "You are an Executive Assistant drafting a professional follow-up email "
            "summarising the meeting and action items.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown."
        ),
        "template": (
            "Draft a follow-up email based on the meeting analysis below.\n\n"
            "Meeting Transcript:\n{{raw_field_1}}\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Stage 2 Action Items:\n{{stage2_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "email_subject": "Subject line for the follow-up email",\n'
            '    "email_body": "Full follow-up email with summary and action items",\n'
            '    "pending_confirmations": ["Item needing confirmation from attendees"],\n'
            '    "notes_for_next_meeting": "Brief notes to carry forward"\n'
            "}"
        ),
    },
})


# ═══════════════════════════════════════════════════════════════
# 5. Recipe Adapter
# ═══════════════════════════════════════════════════════════════

register_preset({
    "key": "recipe_adapter",
    "label": "🍳 Recipe Adapter",
    "description": "Recipe + dietary constraints → adapted recipe with every substitution explained",
    "icon": "🍳",

    "inputs": [
        {"key": "field_1", "label": "Original Recipe", "placeholder": "Paste the full recipe (ingredients + instructions)...", "height": 200},
        {"key": "field_2", "label": "Dietary Constraints", "placeholder": "e.g. gluten-free, vegan, low-carb, nut-free, dairy-free...", "height": 100},
    ],

    "stage1_title": "Parse & Analyse",
    "stage1_technique": "Role Prompting + Structured Output",
    "stage1": {
        "system": (
            "You are a professional chef and nutritionist. Analyse the recipe and "
            "extract a structured overview of its ingredients and nutritional profile.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown.\n"
            "- Use the exact schema provided."
        ),
        "template": (
            "Analyse the following recipe and extract its key characteristics.\n\n"
            "Recipe:\n{{field_1}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "recipe_name": "Name of the recipe",\n'
            '    "cuisine_type": "e.g. Italian, Mexican, fusion",\n'
            '    "ingredients": ["ingredient 1", "ingredient 2"],\n'
            '    "cooking_method": "bake / fry / steam / boil / raw",\n'
            '    "prep_time_minutes": 30,\n'
            '    "difficulty": "easy / medium / hard",\n'
            '    "dietary_tags": ["vegetarian", "contains gluten"]\n'
            "}"
        ),
    },

    "stage2_title": "Plan Substitutions",
    "stage2_technique": "Chain-of-Thought Reasoning",
    "stage2": {
        "system": (
            "You are a professional chef adapting recipes for dietary constraints. "
            "For each substitution, explain why it works nutritionally and culinarily.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown."
        ),
        "template": (
            "Plan ingredient substitutions to satisfy the dietary constraints.\n\n"
            "Dietary Constraints:\n{{raw_field_2}}\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "substitutions": [\n'
            '        {"original": "original ingredient", "replacement": "replacement ingredient",\n'
            '         "reason": "Why this substitution works", "ratio": "1:1 or specific ratio"}\n'
            '    ],\n'
            '    "removed_ingredients": ["ingredient removed entirely with reason"],\n'
            '    "constraints_met": ["Constraint 1 met by...", "Constraint 2 met by..."],\n'
            '    "constraints_not_met": ["Constraint that could not be fully met and why"],\n'
            '    "reasoning": "Step-by-step reasoning"\n'
            "}"
        ),
    },

    "stage3_title": "Generate Adapted Recipe",
    "stage3_technique": "Goal-Oriented Prompting",
    "stage3": {
        "system": (
            "You are a professional chef. Write the full adapted recipe with clear "
            "instructions, including all substitutions.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown."
        ),
        "template": (
            "Generate the full adapted recipe based on the analysis below.\n\n"
            "Original Recipe:\n{{raw_field_1}}\n\n"
            "Dietary Constraints:\n{{raw_field_2}}\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Stage 2 Substitutions:\n{{stage2_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "adapted_recipe_name": "Name reflecting the adaptation",\n'
            '    "adapted_ingredients": ["ingredient 1 (substituted from original)", "ingredient 2"],\n'
            '    "adapted_instructions": "Step-by-step cooking instructions incorporating changes",\n'
            '    "substitution_notes": "Summary of all substitutions and why they work",\n'
            '    "nutritional_notes": "How the adaptation affects nutritional profile / taste / texture",\n'
            '    "tips": "Chef tips for best results with the adapted recipe"\n'
            "}"
        ),
    },
})


# ═══════════════════════════════════════════════════════════════
# 6. Trip Day-Planner
# ═══════════════════════════════════════════════════════════════

register_preset({
    "key": "trip_planner",
    "label": "✈️ Trip Day-Planner",
    "description": "Loose request (city · days · interests · budget) → structured constraints + feasible day-by-day itinerary",
    "icon": "✈️",

    "inputs": [
        {"key": "field_1", "label": "Trip Request", "placeholder": "Describe your trip: destination city, number of days, interests, budget, travel style...", "height": 180},
        {"key": "field_2", "label": "Additional Preferences (optional)", "placeholder": "Dietary restrictions, mobility concerns, time of year, must-see attractions...", "height": 100},
    ],

    "stage1_title": "Extract Constraints",
    "stage1_technique": "Role Prompting + Structured Output",
    "stage1": {
        "system": (
            "You are a professional travel planner. Extract structured constraints "
            "from the user's loose trip request.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown.\n"
            "- Use the exact schema provided."
        ),
        "template": (
            "Extract structured travel constraints from the following trip request.\n\n"
            "Request:\n{{field_1}}\n\n"
            "Preferences:\n{{field_2}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "destination": "City, Country",\n'
            '    "days": 3,\n'
            '    "travel_style": "budget / mid-range / luxury",\n'
            '    "interests": ["history", "food", "nature", "shopping", "culture"],\n'
            '    "budget_range": "low / medium / high",\n'
            '    "special_requirements": ["vegan", "wheelchair accessible"],\n'
            '    "best_time_to_visit": "Seasonal recommendation based on destination"\n'
            "}"
        ),
    },

    "stage2_title": "Design Itinerary",
    "stage2_technique": "Chain-of-Thought Reasoning",
    "stage2": {
        "system": (
            "You are a professional travel planner designing a day-by-day itinerary. "
            "Balance activities, travel time, meals, and rest. Use Chain-of-Thought reasoning.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown."
        ),
        "template": (
            "Design a feasible day-by-day itinerary based on the extracted constraints.\n\n"
            "Stage 1 Analysis:\n{{stage1_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "itinerary": [\n'
            '        {\n'
            '            "day": 1,\n'
'            "date": "Suggested date or Day 1",\n'
            '            "morning": "Morning activity",\n'
            '            "afternoon": "Afternoon activity",\n'
            '            "evening": "Evening activity / dinner",\n'
            '            "meal_suggestions": ["Breakfast spot", "Lunch spot", "Dinner spot"],\n'
            '            "travel_tips": "Transportation notes for the day"\n'
            '        }\n'
            '    ],\n'
            '    "budget_estimate": "Estimated total cost range",\n'
            '    "packing_tips": "What to pack based on activities and season",\n'
            '    "reasoning": "Step-by-step reasoning behind the itinerary design"\n'
            "}"
        ),
    },

    "stage3_title": "Finalise & Polish",
    "stage3_technique": "Goal-Oriented Prompting",
    "stage3": {
        "system": (
            "You are a professional travel planner. Polish the itinerary into a "
            "beautiful, readable day-by-day plan with helpful tips.\n\n"
            "Rules:\n- Return ONLY valid JSON.\n- Do NOT wrap in markdown."
        ),
        "template": (
            "Generate the final polished trip plan based on the analysis below.\n\n"
            "Original Request:\n{{raw_field_1}}\n\n"
            "Stage 1 Constraints:\n{{stage1_json}}\n\n"
            "Stage 2 Itinerary:\n{{stage2_json}}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            '{\n'
            '    "trip_title": "Catchy title for the trip",\n'
            '    "overview": "Brief overview of the trip plan",\n'
            '    "daily_plan": "Full readable day-by-day itinerary with highlights",\n'
            '    "budget_breakdown": {"accommodation": "$", "food": "$", "activities": "$", "transport": "$", "total": "$"},\n'
            '    "pro_tips": ["Tip 1", "Tip 2", "Tip 3"],\n'
            '    "alternative_options": "Optional alternatives for key activities"\n'
            "}"
        ),
    },
})