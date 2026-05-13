# ReconAgent

AI-powered bank reconciliation for small businesses. Drop in your invoices, bills, and bank statement — get back a clean Excel audit report.

## What It Does

ReconAgent automates the monthly reconciliation ritual:

1. **Parses** customer invoices, vendor bills, and a bank statement (all PDFs)
2. **Matches** bank credits to invoices (AR) and bank debits to bills (AP) using strict amount + reference-number matching
3. **Generates** an Excel audit report with matched pairs, unmatched lines, and a summary

Precision over recall — a declared match is almost never wrong. Anything uncertain is flagged for human review.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (async) |
| Orchestration | LangGraph StateGraph + Pydantic state models |
| LLM (primary) | Claude Code via `langchain-claude-code` |
| LLM (alternative) | DeepAgents with multi-provider LangChain (OpenAI, Groq, Google, OpenRouter) |
| Validation | Pydantic BaseModel |
| Observability | LangSmith tracing |
| Console | Rich |

## Project Structure

```
src/
├── main.py                  # FastAPI app + API endpoints
├── Graph/
│   └── recon_graph.py       # LangGraph state definition & reconciliation node
├── agent/
│   └── recon_agent.py       # ClaudeAgent and DeepAgent factory functions
└── prompts/
    ├── SYSTEM_PROMPT.md     # System prompt for the reconciliation agent
    └── sample_template.xlsx # Reference Excel template for output
user_files/                  # Financial document storage
├── bills/                   # Vendor bills (PDFs)
└── invoice/                 # Customer invoices (PDFs)
```

## Architecture

```
POST /reconcile-from-folder
        │
        ▼
    FastAPI endpoint
        │
        ▼
  LangGraph StateGraph ── ReconState (Pydantic)
        │
        ▼
    node_recon()
        │
        ▼
  ClaudeAgent() factory ── Claude Code LLM
        │
        ▼
  Excel audit report → output/
```

## Setup

### Prerequisites

- Python 3.13+
- A Claude Code OAuth token (primary) or OpenAI / Groq / Google API key (alternative providers)

### Install

```bash
git clone <repo-url>
cd main_agent_recon
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file in the project root:

```bash
# Required — LLM Access
CLAUDE_CODE_OAUTH_TOKEN=     # Claude Code OAuth token
OPENAI_API_KEY=              # OpenAI API key (for alternative providers)

# Required — Model Configuration
RECON_OPENAI_MODEL=          # Model identifier (alternative provider)
RECON_OPENAI_BASE_URL=       # API base URL (alternative provider)

# Optional — Observability
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=

# Optional — Alternative Providers
GROQ_API_KEY=
OPENROUTER_API_KEY=
```

### Run

```bash
uvicorn src.main:app --reload --port 8000
```

## API

### `POST /reconcile-from-folder`

Reconcile documents from a local folder.

**Request** (form data):

| Field | Required | Description |
|-------|----------|-------------|
| `folder_path` | Yes | Path to folder containing `bills/`, `invoice/`, and a bank statement PDF |
| `user_prompt` | No | Custom reconciliation instructions |

**Expected folder layout:**

```
session_folder/
├── bills/            # Vendor bills (PDFs)
├── invoice/          # Customer invoices (PDFs)
└── statement.pdf     # Bank statement (single PDF)
```

**Response:**

```json
{
  "session_dir": "/path/to/session",
  "output_dir": "/path/to/session/output",
  "bank_statement": "/path/to/statement.pdf",
  "agent_response": "Reconciliation results..."
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/reconcile-from-folder \
  -F "folder_path=./user_files" \
  -F "user_prompt=Reconcile these documents"
```

## Reconciliation Logic (v1)

**Two-way strict matching:**

- Bank **credits** (inflows) → matched against **invoices** (AR)
- Bank **debits** (outflows) → matched against **bills** (AP)

A bank line matches a document **iff**:
1. Amounts are exactly equal, **and**
2. The document's reference number appears in the bank line description

No fuzzy matching in v1. Unmatched items are surfaced for human review.

## Performance Metrics 

1. 4000 points --> Codex 
2. 4000 points ---> Claude 
3. 2000 points --> Human review 

After running @Performance_metrics prompt with Codex and Claude output are in @codex_PM.json, @claude_PM.json 

total score : 3576 + 3040 + 1300 = 7916


### Human Rating Rubric (2000 pts)

Use this yourself or give it to your reviewer:

| Category | Max | Your Score |
|---|---:|---:|
| Does the output feel trustworthy to a finance person? | 1000 | 900 |
| Would you submit this to a real auditor without shame? | 500 | 100 |
| Speed & practicality (ran without crashes, usable output) | 500 | 300 |