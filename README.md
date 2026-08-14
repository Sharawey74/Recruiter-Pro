<div align="center">

# Recruiter Pro 

**Next-Generation Intelligent Applicant Tracking System**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.3.0-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4.2-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

[![Ollama](https://img.shields.io/badge/Ollama-LLM-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.13-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success?style=for-the-badge&logo=statuspage&logoColor=white)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Sharawey74/Recruiter-Pro-AI/pulls)

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API Reference](#-api-reference) • [Contributing](#-contributing)

</div>

---

## 📋 Overview

**Recruiter Pro** is a cutting-edge Applicant Tracking System that leverages a sophisticated **4-agent AI pipeline** to automatically parse, analyze, score, and explain resume-job matches. Built with modern technologies and powered by local LLMs, it provides accurate, explainable, and privacy-focused recruitment automation.

### Why Recruiter Pro ?

<table>
<tr>
<td align="center" width="33%">
<h3>🤖</h3>
<b>AI-Powered Matching</b>
<br><br>Hybrid scoring combining keyword, semantic, and skill-based analysis
</td>
<td align="center" width="33%">
<h3>🔒</h3>
<b>Privacy-First</b>
<br><br>All processing happens locally with Ollama - no data leaves your infrastructure
</td>
<td align="center" width="33%">
<h3>⚡</h3>
<b>Lightning Fast</b>
<br><br>Processes resumes in seconds with real-time results
</td>
</tr>
<tr>
<td align="center" width="33%">
<h3>🎯</h3>
<b>Explainable AI</b>
<br><br>Get detailed explanations for every match decision
</td>
<td align="center" width="33%">
<h3>🌐</h3>
<b>Modern UI</b>
<br><br>Beautiful, responsive Next.js interface with real-time updates
</td>
<td align="center" width="33%">
<h3>🔧</h3>
<b>Tested</b>
<br><br>344 tests, green in CI, with the scoring path verified against a fixed corpus
</td>
</tr>
</table>

---

## ✨ Features

### 📄 Multi-Format Resume Parsing
- ✅ PDF, DOCX support with intelligent text extraction
- ✅ Automatic section detection (experience, education, skills)
- ✅ Contact information extraction

### 🧠 4-Agent AI Pipeline
1. **Agent 1 (Parser)**: Extract structured data from resumes
2. **Agent 2 (Extractor)**: Rule-based feature extraction (regex, NLTK)
3. **Agent 3 (Scorer)**: Hybrid scoring algorithm
   - Skill matching (50%), against a controlled vocabulary of 679 skills
   - Job-title similarity (17%)
   - Experience fit (20%), education (8%), keyword overlap (5%)
   - Optionally blended with an ML model (see *Known limitations*)
4. **Agent 4 (Explainer)**: Generate human-readable insights

### 🎨 Dual AI Modes
- 🔹 **Standard Search**: Fast rule-based matching
- 🔹 **Comprehensive AI**: Advanced LangChain-powered analysis

### 📊 Rich Visualizations
- 📈 Circular progress indicators for match scores
- 🏷️ Skill comparison with matched/missing badges
- 🔄 Real-time result updates

### 🎯 Scoring System

<div align="center">

Our hybrid scoring algorithm combines three approaches:

</div>

| Component | Weight | Description |
|-----------|:------:|-------------|
| **⚙️ Skill Match** | 50% | CV skills against the job's required and preferred skills, both resolved to a controlled vocabulary |
| **💼 Experience** | 20% | Years of experience against the job's range |
| **🏷️ Title Similarity** | 17% | Candidate's role against the job title |
| **🎓 Education** | 8% | Highest degree against the stated requirement |
| **🔤 Keyword Match** | 5% | Terms from the job description present in the CV |

These weights live in `config/agents.yaml` and nowhere else. There is no
semantic-similarity component; earlier versions of this README described one.

<div align="center">

**Rule-based score** = Skill×0.50 + Title×0.17 + Experience×0.20 + Education×0.08 + Keyword×0.05

**Final score** = Rule-based×0.60 + ML×0.40 *(rule-based alone when no model is loaded)*

</div>

---

## ⚠️ Scope and known limitations

Stated plainly, because a matching system that overstates its confidence is
worse than one that admits its bounds.

### The ML half contributes almost no ranking signal

The hybrid score is 60% rule-based and 40% ML. Measured against the real
corpus, for a fixed CV **the model returns only three distinct probabilities
across all 800 jobs** — the only per-job feature it sees is the job title. So
the ML term shifts scores nearly uniformly rather than ordering them. **The
ranking you see is effectively the rule-based score.**

### The training dataset cannot produce an honest ATS model

`Recruiter Decision` in the source dataset is a pure threshold on `AI Score`
(≥65 → Hire) — 100% accuracy from one column. `AI Score` is excluded from
training, but the remaining columns reconstruct the decision anyway:
**`Experience` alone reaches ROC-AUC 0.9244; `Experience + Projects Count`
reaches 0.9933.** Two ordinary columns.

The reported metrics (precision 1.000, ROC-AUC 1.000) are therefore a property
of the dataset, not evidence of a good model. Removing features does not fix
it — the task is trivial by construction. This is reported rather than papered
over, because the honest framing is more useful than a number nobody should
believe.

### The corpus is synthetic

The 800 job descriptions were generated against the controlled vocabulary so
that skill matching has something coherent to match against. They are
realistic, not real. Descriptions deliberately avoid restating the structured
skill list, so keyword scoring cannot trivially recover it.

### Not evaluated for hiring fairness

There is no bias audit, no adverse-impact testing, and no protected-attribute
analysis. **This is a portfolio and learning project — it should not be used to
make real hiring decisions.**

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18 or higher
- **Ollama** (for local LLM)

### Installation

```bash
# Clone the repository
git clone https://github.com/Sharawey74/Recruiter-Pro-AI.git
cd Recruiter-Pro-AI

# Install Python dependencies
pip install -r requirements.txt

# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull LLM model
ollama pull llama3.2:3b

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Running the Application

#### Option 1: One command (recommended)

```powershell
.\run.ps1
```

Starts the backend and the frontend together, waits until each is genuinely
answering, streams both logs into the one window with an `[api]` / `[web]`
prefix, and stops both on Ctrl-C. It reports what the backend actually loaded
— the corpus size, and whether hybrid ML scoring is running or it fell back to
rules — because both degrade silently.

| Flag | Effect |
|---|---|
| `-Prod` | Build and serve the production bundle instead of the dev server |
| `-ApiPort` / `-WebPort` | Use different ports. CORS and `NEXT_PUBLIC_API_URL` follow automatically |
| `-Force` | Stop whatever holds a port first — only that process, never by name |
| `-NoBrowser` | Do not open a browser |

Logs are written to `logs/api.log` and `logs/web.log`.

No LLM is required. The rule-based explanation provider is first-class
(see [ADR-2](docs/adr/)), so the app runs with no Ollama, no API key and no
quota. Configure a provider in `.env` if you want written explanations.

#### Option 2: Manual startup

```bash
# Terminal 1: Backend
python -m uvicorn src.api:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🏗️ Architecture

<div align="center">

### System Overview

![Architecture](https://img.shields.io/badge/Architecture-3--Tier-blue?style=for-the-badge&logo=diagram&logoColor=white)
![Pattern](https://img.shields.io/badge/Pattern-Monolithic-green?style=for-the-badge&logo=cube&logoColor=white)
![Design](https://img.shields.io/badge/Design-SOLID%20Principles-orange?style=for-the-badge&logo=code&logoColor=white)

</div>

```
┌──────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                         │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Next.js Frontend (React + TypeScript)            │  │
│  │  Port: 3000                                        │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────────────┘
                     │ REST API
                     ↓
┌──────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend (Python + Uvicorn)               │  │
│  │  Port: 8000                                        │  │
│  │                                                    │  │
│  │  ┌──────────────────────────────────────────────┐ │  │
│  │  │      4-Agent Pipeline Orchestrator           │ │  │
│  │  │                                              │ │  │
│  │  │  Agent 1: Parser                            │ │  │
│  │  │      ↓                                       │ │  │
│  │  │  Agent 2: Extractor (NLP)                   │ │  │
│  │  │      ↓                                       │ │  │
│  │  │  Agent 3: Scorer (Hybrid Algorithm)         │ │  │
│  │  │      ↓                                       │ │  │
│  │  │  Agent 4: Explainer (LLM)                   │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────────┐
      ↓              ↓                  ↓
┌──────────┐  ┌──────────────┐  ┌──────────────┐
│ AI/LLM   │  │   Database   │  │ File Storage │
│          │  │              │  │              │
│ Ollama   │  │  SQLite      │  │ JSON/CSV     │
│ Llama3.2 │  │  (Optional)  │  │ Files        │
│ Port:    │  │              │  │              │
│ 11500    │  │              │  │              │
└──────────┘  └──────────────┘  └──────────────┘
```

### 🏛️ Architecture Type

**Monolithic Application with Modular Agent Pattern**

This system is a **monolithic architecture** rather than microservices:

- ✅ **Single Deployment Unit**: The entire backend runs as one FastAPI application
- ✅ **Shared Process**: All 4 agents operate within the same process and memory space
- ✅ **Internal Communication**: Agents communicate via direct function calls (not HTTP/network)
- ✅ **Modular Design**: Agents are organized as separate modules for maintainability
- ✅ **Simple Deployment**: One backend service, one frontend service, one LLM service

**Why Monolithic?**
- Faster development and testing
- Lower latency (no network calls between agents)
- Simpler deployment and monitoring
- Easier debugging and troubleshooting
- Sufficient for current scale and requirements

**Architecture Pattern**: The 4-agent pipeline follows the **Pipeline Pattern** where data flows sequentially through independent processing stages, all within a single application.

### 4-Agent Pipeline

<div align="center">

**Sequential Data Processing Flow**

</div>

| Stage | Agent | Purpose | Technology Stack |
|:-----:|-------|---------|------------------|
| **1** | 🔍 **Parser** | Parse PDF/DOCX files | ![PDFMiner](https://img.shields.io/badge/PDFMiner-FF5733?style=flat-square) ![python-docx](https://img.shields.io/badge/python--docx-3776AB?style=flat-square) ![PyMuPDF](https://img.shields.io/badge/PyMuPDF-4CAF50?style=flat-square) |
| **2** | 🧬 **Extractor** | Extract structured data | ![Regex](https://img.shields.io/badge/Regex-FF9800?style=flat-square) ![NLTK](https://img.shields.io/badge/NLTK%203.8.1-2196F3?style=flat-square) |
| **3** | 📊 **Scorer** | Calculate match scores | ![Algorithm](https://img.shields.io/badge/Hybrid%20Algorithm-9C27B0?style=flat-square) ![Scores](https://img.shields.io/badge/40%25%20Keyword%20+%2030%25%20Semantic%20+%2030%25%20Skills-00BCD4?style=flat-square) |
| **4** | 🤖 **Explainer** | Generate AI explanations | ![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat-square&logo=ollama) ![LangChain](https://img.shields.io/badge/LangChain-009688?style=flat-square&logo=chainlink) |

<div align="center">

**Data Flow:** Resume File → Parser → Extractor → Scorer → Explainer → Results

</div>

### Design Patterns

<div align="center">

<table>
<tr>
<td align="center" width="20%">
<img src="https://img.shields.io/badge/🏭-Factory-blue?style=for-the-badge"/>
<br><small>Agent 4 mode selection</small>
</td>
<td align="center" width="20%">
<img src="https://img.shields.io/badge/⛓️-Pipeline-green?style=for-the-badge"/>
<br><small>Sequential processing</small>
</td>
<td align="center" width="20%">
<img src="https://img.shields.io/badge/🎯-Strategy-orange?style=for-the-badge"/>
<br><small>Multiple algorithms</small>
</td>
<td align="center" width="20%">
<img src="https://img.shields.io/badge/📚-Repository-purple?style=for-the-badge"/>
<br><small>Data abstraction</small>
</td>
</tr>
</table>

</div>

---

## 🛠️ Technology Stack

<div align="center">

### Backend Technologies

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-0.24.0-499848?style=for-the-badge&logo=gunicorn&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2.5.0-E92063?style=for-the-badge&logo=pydantic&logoColor=white)

![Ollama](https://img.shields.io/badge/Ollama-0.4.4-000000?style=for-the-badge&logo=ollama&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3.13-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)
![NLTK](https://img.shields.io/badge/NLTK-3.8.1-154F3C?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.1.4-150458?style=for-the-badge&logo=pandas&logoColor=white)

### Frontend Technologies

![Next.js](https://img.shields.io/badge/Next.js-16.3.0-000000?style=for-the-badge&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-18.3.1-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.4.2-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-3.4.1-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

![Axios](https://img.shields.io/badge/Axios-1.6.7-5A29E4?style=for-the-badge&logo=axios&logoColor=white)
![Lucide](https://img.shields.io/badge/Lucide-0.344.0-F56565?style=for-the-badge&logo=lucide&logoColor=white)
![Recharts](https://img.shields.io/badge/Recharts-2.12.2-FF6B6B?style=for-the-badge&logo=chartdotjs&logoColor=white)

</div>

<details>
<summary><b>🔹 Click to expand detailed Backend stack</b></summary>
<br>

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Framework** | FastAPI | 0.104.1 | Modern async web framework |
| **Server** | Uvicorn | 0.24.0 | ASGI server |
| **Validation** | Pydantic | 2.5.0 | Data validation |
| **LLM** | Ollama | 0.4.4 | Local LLM runtime |
| **AI Framework** | LangChain | 0.3.13 | LLM orchestration |
| **Text Processing** | NLTK | 3.8.1 | Stopwords, tokenization |
| **PDF Parser** | PDFMiner.six | 20221105 | PDF text extraction |
| **DOCX Parser** | python-docx | 1.1.0 | Word document parsing |
| **Data** | Pandas | 2.1.4 | Data manipulation |
| **Testing** | pytest | 7.4.3 | Test framework |

</details>

<details>
<summary><b>🔹 Click to expand detailed Frontend stack</b></summary>
<br>

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Framework** | Next.js | 16.3.0 | React framework with SSR |
| **UI Library** | React | 18.3.1 | Component-based UI |
| **Language** | TypeScript | 5.4.2 | Type-safe JavaScript |
| **Styling** | Tailwind CSS | 3.4.1 | Utility-first CSS |
| **HTTP Client** | Axios | 1.6.7 | API communication |
| **Icons** | Lucide React | 0.344.0 | Icon library |
| **Charts** | Recharts | 2.12.2 | Data visualization |
| **File Upload** | React Dropzone | 14.2.3 | Drag-and-drop uploads |
| **Notifications** | Sonner | 1.4.3 | Toast messages |

</details>

---

## 📂 Project Structure

```
Recruiter-Pro-AI/
├── frontend/                 # Next.js Frontend Application
│   ├── app/                  # Next.js App Router
│   │   ├── page.tsx          # Home page (Upload)
│   │   ├── layout.tsx        # Root layout
│   │   ├── globals.css       # Global styles
│   │   ├── upload/           # Upload flow pages
│   │   ├── results/          # Results display
│   │   └── history/          # Match history
│   ├── components/           # React components
│   │   ├── layout/           # Layout components
│   │   ├── ui/               # UI primitives
│   │   └── upload/           # Upload-specific components
│   ├── lib/                  # Utilities and types
│   └── package.json          # Node.js dependencies
│
├── src/                      # Backend Source Code
│   ├── api.py                # FastAPI application
│   ├── ats_engine.py         # ATS matching engine
│   ├── agents/               # 4-Agent Pipeline
│   │   ├── agent1_parser.py          # Document parser
│   │   ├── agent2_extractor.py       # Feature extractor
│   │   ├── agent3_scorer.py          # Hybrid scorer
│   │   ├── agent4_factory.py         # Factory pattern
│   │   ├── agent4_llm_explainer.py   # Direct HTTP explainer
│   │   ├── agent4_langchain_explainer.py  # LangChain explainer
│   │   └── pipeline.py               # Orchestrator
│   ├── core/                 # Core configurations
│   ├── storage/              # Data persistence
│   └── utils/                # Utilities
│
├── data/                     # Data Files
│   ├── json/                 # Job corpus (800 jobs, generated against the skill vocabulary)
│   ├── dictionaries/         # Skills mappings
│   ├── database/             # SQLite (optional)
│   └── AI_Resume_Screening.csv  # Training data
│
├── tests/                    # Test Suite
│   ├── unit/                 # Unit tests (9 files)
│   ├── integration/          # Integration tests (4 files)
│   └── system/               # E2E tests (2 files)
│
├── docs/                     # Documentation
│   ├── DEVELOPER_GUIDE.md    # Complete technical guide
│   ├── ARCHITECTURE.md       # Architecture details
│   └── [40+ documentation files]
│
├── scripts/                  # Utility scripts
├── .gitignore               # Git ignore rules
├── .gitattributes           # Git attributes
├── requirements.txt         # Python dependencies
├── run.ps1                  # Launcher — starts backend + frontend together
└── README.md                # This file
```

---

## 📖 API Reference

### Endpoints

#### `POST /api/match`

Upload resume and match to job position.

**Request:**

```http
POST /api/match HTTP/1.1
Content-Type: multipart/form-data

file: <resume.pdf>
job_id: "job_001"
use_llm: true
use_langchain: true
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "profile": {
      "name": "John Doe",
      "email": "john@example.com",
      "skills": ["Python", "FastAPI", "React"],
      "experience_years": 5
    },
    "scores": {
      "overall_score": 85.5,
      "keyword_score": 78.0,
      "semantic_score": 92.0,
      "skill_score": 88.0,
      "matched_skills": ["Python", "FastAPI", "React"],
      "missing_skills": ["Docker", "Kubernetes"]
    },
    "explanation": "Match analysis: Strong candidate with excellent technical background..."
  }
}
```

#### `GET /jobs`

Get all available job positions.

**Response:**

```json
[
  {
    "job_id": "job_001",
    "job_title": "Software Engineer",
    "company_name": "Tech Corp",
    "location": "San Francisco, CA",
    "skills_required": ["Python", "FastAPI", "Docker"],
    "experience_level": "Mid-Level"
  }
]
```

#### `GET /api/health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "ollama_available": true,
  "jobs_loaded": 800,
  "version": "2.0.0"
}
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run by category
pytest tests/unit/ -v          # Fast unit tests
pytest tests/integration/ -v   # API integration tests
pytest tests/system/ -v        # End-to-end tests

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Test Structure

```
tests/
├── unit/          # 17 files - components in isolation
├── integration/   # 4 files  - API contract, pipeline, agent hand-offs
├── system/        # 1 file   - performance guards
└── fixtures/      # sample CV used by the agent hand-off tests
```

### Coverage

**338 tests, all passing. 77% statement coverage of `src/`** — measured, not
estimated. An earlier version of this README claimed "85%+"; the real figure is
below that, and the uncovered quarter is mostly the ML training path, which the
suite exercises only through small synthetic datasets.

The suite runs in CI on every push and pull request, with no network, no API
key and no model — the rule-based explanation provider exists so that it can.
CI also runs `ruff`, the corpus validator, and a byte-level scan for control
characters in source.

> Until recently a quarter of this suite failed on every run, and 33 of its
> tests could never have passed: 23 targeted an API surface this repository has
> never served, and 10 more collected their measurements inside a condition
> that was never true, so they reported green while asserting nothing. They are
> deleted or rewritten. The count above is tests that can actually fail.

---

## 🎯 Use Cases

### 1. HR Departments
- **Automate initial resume screening**
- **Rank a shortlist in under a second** — measured: 0.74 s for one CV against all 800 jobs
- **Eliminate unconscious bias**
- **Scale recruitment operations**

### 2. Recruitment Agencies
- **Process high volumes efficiently**
- **Provide detailed candidate reports**
- **Match candidates to multiple positions**
- **Track candidate pipelines**

### 3. Job Platforms
- **Instant resume analysis**
- **Job recommendation engines**
- **Candidate-job similarity scores**
- **Automated shortlisting**

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11500
OLLAMA_MODEL=llama3.2:3b
LLM_TIMEOUT=120

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Data Paths
JOBS_DATA_PATH=data/json/jobs.json
SKILLS_DICT_PATH=data/dictionaries/skills_canonical.json
```

### Customization

#### Change LLM Model

```python
# src/core/config.py
LLM_MODEL = "llama3.2:3b"  # Change to any Ollama model
```

#### Adjust Scoring Weights

```python
# src/agents/agent3_scorer.py
# Weights are set in config/agents.yaml under `scoring:`
SEMANTIC_WEIGHT = 0.3  # Default: 30%
SKILL_WEIGHT = 0.3     # Default: 30%
```

---

## 📊 Performance

### ⚡ Benchmarks

| Metric | Value | Description |
|--------|-------|-------------|
| **🚀 Resume Processing** | < 2 seconds | Complete parsing and extraction |
| **🤖 LLM Explanation** | 3-5 seconds | AI-generated insights |
| **⏱️ API Response** | < 7 seconds | End-to-end request processing |
| **🎯 Match Accuracy** | 85-92% | Resume-job matching quality |
| **👥 Concurrent Users** | 50+ | With proper infrastructure |

### 🚀 Performance Optimizations

**Backend Optimizations:**
- ✅ **Job data preloading** on startup (eliminates disk I/O per request)
- ✅ **Async processing** with FastAPI (non-blocking I/O operations)
- ✅ **Concurrent server startup** (3 services launch in 2 seconds)
- ✅ **Efficient text processing** with regex and NLTK
- ✅ **LLM response caching** for repeated queries

**Frontend Optimizations:**
- ✅ **Code splitting** with Next.js (faster page loads)
- ✅ **Server-side rendering** (improved SEO and performance)
- ✅ **Image optimization** (automatic WebP conversion)
- ✅ **Bundle size optimization** (tree-shaking unused code)

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

- 🐛 **Report bugs** via GitHub Issues
- 💡 **Suggest features** in Discussions
- 📝 **Improve documentation**
- 🧪 **Add tests**
- 🔧 **Fix issues** with Pull Requests

### Development Workflow

```bash
# 1. Fork the repository
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/Recruiter-Pro-AI.git

# 3. Create a feature branch
git checkout -b feature/your-feature-name

# 4. Make your changes
# 5. Run tests
pytest tests/ -v

# 6. Format code
black src/ tests/
flake8 src/ tests/

# 7. Commit and push
git commit -m "Add: your feature description"
git push origin feature/your-feature-name

# 8. Open a Pull Request
```

### Code Standards

- Follow **PEP 8** for Python code
- Use **Black** for code formatting
- Write **type hints** for all functions
- Add **docstrings** for public APIs
- Maintain **test coverage** above 80%

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **Next.js** - React framework for production
- **Ollama** - Local LLM runtime
- **LangChain** - LLM orchestration framework

---

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/Sharawey74/Recruiter-Pro-AI/issues)
- **GitHub Discussions**: [Ask questions and share ideas](https://github.com/Sharawey74/Recruiter-Pro-AI/discussions)

---

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!



---

<div align="center">


[⬆ Back to Top](#recruiter-pro)

</div>
