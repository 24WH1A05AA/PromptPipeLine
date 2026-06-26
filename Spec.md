# Prompt Pipeline — Technical Specification

## Overview

Prompt Pipeline is a Streamlit-based application that enables users to chain, transform, and optimize prompts through multiple LLM processing steps. It provides a visual interface for building prompt workflows, with support for template variables, output parsing, and pipeline persistence.

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI (app.py)                   │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Sidebar  │  │ Main Panel   │  │ History / Output     │  │
│  │ Config   │  │ Pipeline     │  │ Display              │  │
│  │ Settings │  │ Builder      │  │                      │  │
│  └────┬─────┘  └──────┬───────┘  └──────────────────────┘  │
└───────┼───────────────┼────────────────────────────────────┘
        │               │
┌───────┴───────────────┴────────────────────────────────────┐
│                    Pipeline Core (pipeline.py)               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Pipeline    │  │ PipelineStep │  │ PipelineManager  │  │
│  │ Orchestrator│  │ Executor     │  │ Persistence      │  │
│  └──────┬──────┘  └──────┬───────┘  └──────────────────┘  │
└─────────┼────────────────┼─────────────────────────────────┘
          │                │
┌─────────┴────────────────┴─────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ LLM Client   │  │ Prompt       │  │ Output Parser    │  │
│  │ (llm.py)     │  │ Templates    │  │ (parser.py)      │  │
│  │              │  │ (prompts.py) │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Module Specifications

### 1. `app.py` — Streamlit Frontend

**Purpose**: Main entry point for the Streamlit application. Handles UI rendering, user interactions, and session state management.

**Key Functions**:
- `init_session_state()` — Initialize Streamlit session state variables for pipeline configuration, step data, and UI state
- `render_sidebar()` — Render configuration panel with API key input, model selection, and pipeline settings
- `render_main_panel()` — Render the pipeline builder interface with step management and execution controls
- `render_history()` — Display saved pipelines and execution history
- `handle_run_pipeline()` — Orchestrate pipeline execution and display results

**Dependencies**: `streamlit`, `pipeline.Pipeline`, `styles.apply_custom_styles`

### 2. `pipeline.py` — Pipeline Orchestration

**Purpose**: Core orchestration logic for managing pipeline steps and execution flow.

**Classes**:
- `PipelineStep` — Represents a single step with a prompt template, optional parser, and execution method
- `Pipeline` — Manages a sequence of steps, handles serialization/deserialization, and coordinates execution
- `PipelineManager` — Handles persistence of multiple pipelines to JSON storage

**Key Methods**:
- `Pipeline.execute()` — Sequentially executes all steps, passing output of one step as input to the next
- `Pipeline.to_dict()` / `from_dict()` — Serialization for pipeline configuration
- `Pipeline.export_to_json()` / `import_from_json()` — File-based persistence

**Dependencies**: `llm.LLMClient`, `prompts.PromptTemplate`, `parser.PromptParser`, `utils`

### 3. `llm.py` — LLM Client

**Purpose**: Client for communicating with the OpenRouter API to perform LLM inference.

**Classes**:
- `LLMClient` — HTTP client for OpenRouter API with methods for listing models, generating text, and streaming
- `LLMResponse` — Wrapper for response data including text, model info, token usage, and cost estimates

**Key Methods**:
- `LLMClient.generate()` — Send prompt to LLM and return complete response
- `LLMClient.generate_stream()` — Stream response chunks for real-time display
- `LLMClient.list_models()` — Fetch available models from OpenRouter
- `LLMClient.count_tokens()` — Estimate token count for a given text

**Dependencies**: `requests`, `python-dotenv`, `os`

### 4. `prompts.py` — Prompt Templates

**Purpose**: Define prompt templates with variable injection and template library management.

**Classes**:
- `PromptTemplate` — Template with `{{variable}}` placeholders, validation, and filling logic
- `PromptLibrary` — Collection of named templates with CRUD operations and JSON persistence
- `SystemPrompt` — System-level prompt configuration for setting LLM behavior

**Key Methods**:
- `PromptTemplate.fill()` — Replace `{{variable}}` placeholders with provided values
- `PromptTemplate.validate()` — Check all required variables are supplied
- `PromptTemplate._extract_variables()` — Parse template to identify variable names

**Dependencies**: `re` (regex), `json`

### 5. `parser.py` — Output Parsers

**Purpose**: Parse and transform raw LLM output into structured data formats.

**Classes**:
- `PromptParser` — Abstract base class for all parsers
- `JSONParser` — Extract and parse JSON from LLM output (handles markdown code blocks)
- `MarkdownParser` — Split markdown into heading-based sections and extract code blocks
- `ListParser` — Split output into list items with optional number stripping
- `ParserRegistry` — Registry of available parsers for selection in the pipeline

**Key Methods**:
- `JSONParser._extract_json_string()` — Find JSON within markdown code fences or plain text
- `MarkdownParser.extract_code_blocks()` — Extract code blocks with language identifiers
- `ListParser._strip_list_numbers()` — Remove leading numbering from list items

**Dependencies**: `json`, `re` (regex)

### 6. `utils.py` — Utility Functions

**Purpose**: Shared helper functions for file I/O, configuration, and common operations.

**Key Functions**:
- `load_json()` / `save_json()` — JSON file read/write with error handling
- `load_pipeline_config()` / `save_pipeline_config()` — Pipeline-specific config persistence
- `load_environment_variables()` — Load `.env` file into dictionary
- `sanitize_filename()` — Remove invalid filename characters
- `truncate_text()` — Text truncation with configurable suffix
- `format_timestamp()` — Unix timestamp to human-readable string
- `estimate_cost()` — API cost estimation based on token counts and model pricing
- `validate_api_key()` — Basic API key format validation
- `create_backup()` — Timestamped file backup
- `list_json_files()` — Directory JSON file listing

**Dependencies**: `json`, `os`

### 7. `styles.py` — Custom Styles

**Purpose**: CSS customization and UI theme management for the Streamlit application.

**Key Functions**:
- `apply_custom_styles()` — Inject custom CSS into the Streamlit app
- `get_custom_css()` — Return CSS string for application styling
- `set_dark_theme()` / `set_light_theme()` — Theme switching
- `style_metric_card()` — Render styled metric display cards
- `style_status_badge()` — Generate HTML for colored status badges
- `style_step_container()` — Generate HTML for pipeline step containers

**Dependencies**: `streamlit`

## Data Flow

```
User Input → Pipeline Builder → Pipeline.execute()
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
                Step 1          Step 2          Step N
                ┌──────┐       ┌──────┐       ┌──────┐
                │Prompt│       │Prompt│       │Prompt│
                │Fill  │──────►│Fill  │──────►│Fill  │
                └──┬───┘       └──┬───┘       └──┬───┘
                   │              │              │
                   ▼              ▼              ▼
               LLM Call       LLM Call       LLM Call
                   │              │              │
                   ▼              ▼              ▼
               Parse Out      Parse Out      Parse Out
                ┌──┴──┐       ┌──┴──┐       ┌──┴──┐
                │Output│       │Output│       │Output│
                └──────┘       └──────┘       └──────┘
                                    │
                                    ▼
                            Final Result Display
```

## API Integration

### OpenRouter API Endpoints

- `GET /api/v1/models` — List available models
- `POST /api/v1/chat/completions` — Generate chat completions
- `POST /api/v1/completions` — Generate text completions

### Request Format

```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "{{prompt}}"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false
}
```

## Configuration

### Environment Variables (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | — | OpenRouter API key |
| `OPENROUTER_DEFAULT_MODEL` | No | `gpt-3.5-turbo` | Default LLM model |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | Custom API base URL |
| `REQUEST_TIMEOUT` | No | `60` | API request timeout (seconds) |
| `MAX_TOKENS` | No | `2048` | Maximum generation tokens |
| `DEFAULT_TEMPERATURE` | No | `0.7` | Default temperature setting |

## Future Enhancements

- [ ] Pipeline branching and conditional logic
- [ ] Batch processing of multiple inputs
- [ ] Export results to CSV/PDF
- [ ] Custom parser plugins
- [ ] Pipeline scheduling and automation
- [ ] Token usage analytics dashboard
- [ ] Collaborative pipeline sharing