# 🧠 Prompt Pipeline

> A multi-stage AI prompt engineering application that transforms raw bug reports into structured developer reports through a chain of specialised prompts.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)
![OpenRouter](https://img.shields.io/badge/OpenRouter-API-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Overview

Prompt Pipeline demonstrates how complex AI tasks can be solved using **multiple specialised prompts** instead of one large prompt.

Rather than asking a single LLM to do everything, the application divides the work into three independent stages. Each stage performs one responsibility and passes structured JSON to the next, making the workflow modular, transparent, and reliable.

Built as part of the **GenAI & Agentic AI Engineering — Day 2 Homework**.

---

## Prompt Engineering Techniques

| Stage | Technique | Responsibility |
|-------|-----------|---------------|
| 1 | Role Prompting + Structured Output | Extract bug metadata into validated JSON |
| 2 | Chain-of-Thought Reasoning | Diagnose severity, priority, and root cause |
| 3 | Goal-Oriented Prompting | Generate fix recommendation and developer report |

---

## Features

- **3-stage prompt pipeline** — Understand → Analyze → Generate
- **JSON handoff** — each stage receives and produces validated JSON
- **Retry parser** — re-prompts the LLM up to 3 times on invalid JSON output
- **3 built-in sample bug reports** — Unicode error, DB timeout, JWT KeyError
- **Execution summary** — elapsed time, model, timestamp displayed after each run
- **Download report** — exports the full pipeline output as a JSON file
- **Graceful error handling** — auth, rate limit, timeout, network, and validation errors all produce clear user messages
- **Modern dark UI** — syntax-highlighted JSON, markdown rendering, progress bar, stage badges

---

## Project Structure

```
PromptPipeline/
├── app.py           # Streamlit frontend — UI, inputs, outputs, execution
├── pipeline.py      # run_pipeline() orchestrator + Pipeline class
├── llm.py           # OpenRouter API client (call_llm, LLMClient)
├── prompts.py       # Prompt templates for all three stages
├── stage1.py        # Stage 1: Understand & Extract
├── stage2.py        # Stage 2: Analyze & Reason
├── stage3.py        # Stage 3: Generate Report
├── parser.py        # parse_json() with 3-attempt retry logic
├── utils.py         # File I/O, formatting, cost estimation helpers
├── styles.py        # Custom CSS — dark theme, cards, badges
├── requirements.txt # Pinned Python dependencies
├── .env.example     # Environment variable template
└── spec.md          # Technical specification
```

---

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/prompt-pipeline.git
cd prompt-pipeline
```

**2. Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure your API key**

```bash
cp .env.example .env
# Edit .env — add your OpenRouter API key
```

```env
OPENROUTER_API_KEY=sk-or-...
MODEL=openai/gpt-4o-mini
```

Get a free API key at [openrouter.ai/keys](https://openrouter.ai/keys).

**5. Run the application**

```bash
streamlit run app.py
```

---

## Pipeline Stages

### Stage 1 — Understand & Extract
**Technique:** Role Prompting + Structured Output

The LLM acts as a Senior Debugging Engineer. It reads the raw bug report and stack trace and returns a validated JSON object:

```json
{
  "title": "UnicodeEncodeError on Windows when saving Unicode filename",
  "description": "...",
  "error_type": "UnicodeEncodeError",
  "affected_module": "file_writer.py",
  "environment": "Windows 10, Python 3.11, cp1252",
  "steps_to_reproduce": ["Open Save As dialog", "Enter filename with accent char", "Click Save"],
  "stack_trace_summary": "Fails at open() in encodings/cp1252.py line 19"
}
```

### Stage 2 — Analyze & Reason
**Technique:** Chain-of-Thought Reasoning

The LLM walks through a structured reasoning chain — error type → severity impact → root cause → confidence — then returns:

```json
{
  "severity": "high",
  "priority": "high",
  "root_cause": "Python uses the OS default encoding (cp1252) instead of UTF-8",
  "confidence": "high",
  "reasoning": "Step 1: UnicodeEncodeError is a runtime crash... Step 2: ..."
}
```

### Stage 3 — Generate Report
**Technique:** Goal-Oriented Prompting

Given the Stage 1 and Stage 2 outputs, the LLM produces a developer-ready fix document:

```json
{
  "recommended_fix": "Change open(filename, 'w') to open(filename, 'w', encoding='utf-8')",
  "developer_notes": "Also set PYTHONUTF8=1 as an environment variable...",
  "testing_strategy": "Test with filenames containing: accented chars, CJK, emoji...",
  "final_report": "A UnicodeEncodeError occurs when..."
}
```

---

## Error Handling

| Error | User Message |
|-------|-------------|
| Missing API key / 401 | 🔑 Authentication failed |
| Rate limit / 402 / 429 | ⏳ Rate limit exceeded |
| Request timeout | ⌛ Request timed out |
| Network failure | 🌐 Network error |
| Invalid JSON from LLM (after 3 retries) | ⚠️ Stage N validation failed |
| Any other exception | ❌ Unexpected error |

---

## Sample Bug Reports

Three samples are available from the dropdown in the UI:

1. **Unicode Encode Error** — `UnicodeEncodeError` on Windows when saving a filename with accented characters
2. **Database Connection Timeout** — SQLAlchemy `OperationalError` due to exhausted connection pool under load
3. **JWT Token KeyError** — `KeyError: 'sub'` in auth middleware after a deployment changed token structure

---

## Assignment Checklist

- ✅ Three prompt stages (Understand, Analyze, Generate)
- ✅ JSON handoff between stages
- ✅ Chain-of-Thought reasoning stage (Stage 2)
- ✅ Structured output prompting (Stage 1)
- ✅ Goal-oriented prompting (Stage 3)
- ✅ Invalid JSON retry mechanism (up to 3 attempts)
- ✅ Three distinct test/sample bug reports
- ✅ Stage-wise execution with per-stage results
- ✅ Execution summary (time, model, timestamp)
- ✅ Download report button

---

## Requirements

```
streamlit==1.35.0
requests==2.32.3
python-dotenv==1.0.1
```

No other dependencies. The syntax highlighter, markdown renderer, and JSON formatter are all built in.

---

## Author

**Lakshmi Vyshnavi**  
B.Tech Computer Science Engineering  
GenAI & Agentic AI Engineering Student Programme

---

## License

Developed for educational purposes. Free to fork, learn from, and build upon.
