# 🧠 Prompt Pipeline

A modular AI Prompt Engineering project demonstrating how complex tasks can be solved by chaining multiple prompts together instead of relying on a single large prompt.

Built as part of the **GenAI & Agentic AI Engineering – Day 2 Homework**.

---

# 🚀 Overview

This project implements a multi-stage AI pipeline where each prompt has a single responsibility.

Instead of asking one massive prompt to solve everything, the system:

1. Understands the bug
2. Reasons about the issue
3. Generates a solution
4. (Optional) Reviews itself

Each stage exchanges structured JSON, making the workflow reliable, modular, and easy to debug.

---

# ✨ Features

## Prompt Engineering

- Multi-stage Prompt Pipeline
- Prompt Chaining
- Modular Prompt Design
- Role Prompting
- Chain-of-Thought Reasoning
- Goal-Oriented Prompting
- Structured JSON Outputs
- Self-Critique Stage (Optional)

---

## AI Workflow

- Bug Understanding
- Root Cause Analysis
- Severity Classification
- Priority Assignment
- Fix Recommendation
- Developer Report Generation

---

## Reliability

- Automatic JSON Parsing
- JSON Validation
- Retry on Invalid JSON
- Graceful Error Handling
- Missing Field Recovery
- Input Validation

---

## Developer Experience

- Clean Console Logs
- Stage-wise Outputs
- Pretty Printed JSON
- Pipeline Summary
- Execution Timing
- Modular Codebase

---

# 📌 Pipeline Architecture

```
User Input
      │
      ▼
Stage 1
Understand
      │
      ▼
Structured JSON
      │
      ▼
Stage 2
Reason
      │
      ▼
Structured JSON
      │
      ▼
Stage 3
Generate Solution
      │
      ▼
Developer Report
      │
      ▼
(Optional)
Self Review
```

---

# 🏗️ Project Structure

```
PromptPipeline/

│

├── prompts/

│ ├── stage1.txt

│ ├── stage2.txt

│ ├── stage3.txt

│ └── stage4.txt

│

├── main.py

├── parser.py

├── pipeline.py

├── utils.py

├── requirements.txt

├── README.md

└── spec.md
```

---

# ⚙️ Technologies

- Python
- OpenRouter API
- JSON
- Prompt Engineering
- Requests

---

# 📋 Pipeline Stages

## Stage 1 – Understand

Extracts:

- Error type
- Module
- Stack trace
- Environment
- Steps to reproduce

Technique:
- Role Prompting
- Structured Output

---

## Stage 2 – Analyze

Determines:

- Severity
- Priority
- Root cause
- Confidence

Technique:
- Chain-of-Thought

---

## Stage 3 – Generate

Creates:

- Suggested fix
- Testing strategy
- Developer report

Technique:
- Goal-Oriented Prompting

---

## Stage 4 (Optional)

Reviews:

- Accuracy
- Completeness
- Hallucinations
- Improvement Suggestions

---

# 🛡 Error Handling

- Invalid JSON Retry
- Missing Fields Recovery
- Empty Input Validation
- Unsupported Language Handling
- Confidence Scoring

---

# 📊 Example Output

```
Input
↓

Extract Bug Details
↓

Analyze Root Cause
↓

Classify Severity
↓

Generate Fix
↓

Developer Report
```

---

# 🎯 Assignment Requirements Covered

- ✅ 3 Prompt Stages
- ✅ JSON Handoff
- ✅ Structured Outputs
- ✅ Chain-of-Thought
- ✅ Goal-Oriented Prompting
- ✅ Retry Mechanism
- ✅ Three Test Cases
- ✅ Invalid Input Handling
- ✅ Reflection

---

# 🌟 Stretch Features

- Self-Critique Stage
- Multiple Model Support
- Prompt Versioning
- Pipeline Metrics
- Confidence Scores
- Execution Timer
- JSON Schema Validation

---

# 📄 License

Created for educational purposes as part of the GenAI & Agentic AI Engineering Program.
