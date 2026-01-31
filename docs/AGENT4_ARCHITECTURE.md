# 🏗️ Agent 4 Architecture Explained

## 📋 Overview

You have **3 files** for Agent 4, but they are **NOT separate scripts** to run. They work together as a **modular architecture** with two operating modes.

---

## 🎯 The Three Files

### 1️⃣ **agent4_llm_explainer.py** (ORIGINAL - 407 lines)
**Status:** ✅ Already exists, fully working

**Purpose:** The **original** Agent 4 implementation using **Direct HTTP** to Ollama

**How it works:**
```python
# Direct HTTP POST request
response = requests.post(
    "http://localhost:11500/api/generate",
    json={"model": "qwen2.5:latest", "prompt": "..."}
)
```

**Advantages:**
- ✅ Fast (no framework overhead)
- ✅ Simple (just HTTP requests)
- ✅ Lightweight (no extra dependencies)
- ✅ Proven and working

**Class:**
```python
class LLMExplainerAgent:
    """Original implementation with Direct HTTP"""
    def generate_explanation(self, match_result) -> str:
        # Uses requests.post() directly
```

---

### 2️⃣ **agent4_langchain_explainer.py** (NEW - 248 lines)
**Status:** 🆕 Just created, needs testing

**Purpose:** **Alternative** Agent 4 implementation using **LangChain framework**

**How it works:**
```python
# LangChain LCEL (Expression Language) chain
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

self.llm = ChatOllama(model="qwen2.5:latest", base_url="...")
self.prompt = PromptTemplate(...)
self.chain = prompt | llm | StrOutputParser()

# One line to generate
explanation = self.chain.invoke(input_data)
```

**Advantages:**
- ✅ Cleaner code with prompt templates
- ✅ Streaming support (real-time responses)
- ✅ Easy to switch providers (Ollama → OpenAI → Claude)
- ✅ Built-in retry logic and error handling
- ✅ LangSmith tracing for debugging

**Class:**
```python
class LangChainExplainerAgent:
    """Advanced implementation with LangChain"""
    def generate_explanation(self, match_result) -> str:
        # Uses LangChain LCEL chain
```

---

### 3️⃣ **agent4_factory.py** (NEW - 60 lines)
**Status:** 🆕 Just created, **CRITICAL** for switching

**Purpose:** **Factory Pattern** - Decides which Agent 4 to use

**How it works:**
```python
def get_explainer_agent(use_langchain=None, config=None):
    """
    Smart selection logic:
    1. If use_langchain=True → Try LangChain (fallback to Direct HTTP)
    2. If use_langchain=False → Use Direct HTTP
    3. If use_langchain=None → Check config.llm.use_langchain
    """
    if use_langchain:
        try:
            from .agent4_langchain_explainer import LangChainExplainerAgent
            return LangChainExplainerAgent(config)  # Advanced mode
        except ImportError:
            # LangChain not installed, fallback
            pass
    
    # Default: Fast mode
    from .agent4_llm_explainer import LLMExplainerAgent
    return LLMExplainerAgent(config)
```

**This is the "brain" that chooses which Agent 4 to use!**

---

## 🔄 How They Work Together

### Architecture Diagram:

```
┌─────────────────────────────────────────────────────────┐
│                    pipeline.py                          │
│  (The main orchestrator that calls agents)              │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ Imports and calls:
                         │ from .agent4_factory import get_explainer_agent
                         │ self.agent4 = get_explainer_agent(config)
                         ▼
┌─────────────────────────────────────────────────────────┐
│              agent4_factory.py                          │
│         (Decides which Agent 4 to use)                  │
│                                                          │
│  if use_langchain=True:                                 │
│      return LangChainExplainerAgent ──────┐             │
│  else:                                    │             │
│      return LLMExplainerAgent ────┐       │             │
└────────────────────────────────────┼───────┼─────────────┘
                                     │       │
                ┌────────────────────┘       └──────────────┐
                ▼                                           ▼
┌──────────────────────────────┐      ┌──────────────────────────────┐
│  agent4_llm_explainer.py     │      │ agent4_langchain_explainer.py│
│  (Direct HTTP - Fast Mode)   │      │  (LangChain - Advanced Mode) │
│                              │      │                              │
│  Uses: requests.post()       │      │  Uses: ChatOllama + LCEL     │
│  Endpoint: localhost:11500   │      │  Endpoint: localhost:11500   │
│  Speed: ⚡ Fast (200ms)      │      │  Speed: 🔗 Moderate (300ms)  │
│  Dependencies: requests      │      │  Dependencies: langchain     │
└──────────────────────────────┘      └──────────────────────────────┘
```

---

## 🚦 Execution Flow

### Example 1: User uploads CV with **Direct HTTP** mode (default)

```
1. User uploads CV via frontend
   ↓
2. Frontend calls API: /match?use_langchain=false
   ↓
3. api.py receives request
   ↓
4. pipeline.py runs 4 agents:
   - Agent 1: Parse CV → text extraction ✅
   - Agent 2: Extract data → structured profile ✅
   - Agent 3: Score matches → calculate scores ✅
   - Agent 4: Explain → factory.get_explainer_agent(use_langchain=False)
   ↓
5. agent4_factory.py sees use_langchain=False
   ↓
6. Returns: LLMExplainerAgent (Direct HTTP)
   ↓
7. agent4_llm_explainer.py generates explanation
   - Uses: requests.post("http://localhost:11500/api/generate")
   - Speed: ⚡ 200ms
   ↓
8. Returns explanation to frontend
```

### Example 2: User uploads CV with **LangChain** mode

```
1. User uploads CV via frontend
   ↓
2. User toggles "🔗 LangChain Mode" ON
   ↓
3. Frontend calls API: /match?use_langchain=true
   ↓
4. api.py swaps agent4 for this request only
   ↓
5. pipeline.py runs Agent 4:
   - Calls: factory.get_explainer_agent(use_langchain=True)
   ↓
6. agent4_factory.py sees use_langchain=True
   ↓
7. Tries to import and return: LangChainExplainerAgent
   - If import fails (langchain not installed) → fallback to Direct HTTP
   - If import succeeds → return LangChain agent
   ↓
8. agent4_langchain_explainer.py generates explanation
   - Uses: ChatOllama LCEL chain
   - Endpoint: still http://localhost:11500 (same Ollama)
   - Speed: 🔗 300ms (slightly slower due to framework overhead)
   ↓
9. Returns explanation to frontend
```

---

## ❓ FAQ: Your Questions Answered

### Q1: Are these separate scripts I need to run?
**A: NO!** They are **modules** (Python classes) that work together automatically.

- ❌ **NOT** like: `python agent4_factory.py` (don't run this)
- ✅ **YES** like: Pipeline imports and uses them automatically

### Q2: Do I need to implement them as scripts?
**A: NO!** They are already implemented as **classes/functions** inside your pipeline.

- Pipeline imports them: `from .agent4_factory import get_explainer_agent`
- API uses them: `pipeline.agent4.generate_explanation(...)`

### Q3: Which one is actually running?
**A: Depends on the toggle in the frontend!**

- **Default:** agent4_llm_explainer.py (Direct HTTP - Fast) ⚡
- **Toggle ON:** agent4_langchain_explainer.py (LangChain - Advanced) 🔗

### Q4: Do I need all three files?
**A: YES, they work as a team:**

1. **agent4_factory.py** - The "decider" (chooses which agent)
2. **agent4_llm_explainer.py** - Fast mode implementation
3. **agent4_langchain_explainer.py** - Advanced mode implementation

### Q5: What happens if I delete one file?
- Delete **factory** → ❌ Pipeline breaks (can't find agent4)
- Delete **llm_explainer** → ❌ Direct HTTP mode breaks
- Delete **langchain_explainer** → ⚠️ LangChain mode breaks, but Direct HTTP still works (fallback)

### Q6: How do I switch modes?
**Three ways:**

**Method 1: Frontend Toggle (Per-Request)**
```typescript
// Frontend: page.tsx
const [useLangChain, setUseLangChain] = useState(false);

// Toggle visible when AI Mode is ON
{useLLM && (
  <div>🔗 LangChain Mode toggle</div>
)}
```

**Method 2: Config File (Global Default)**
```python
# config.py
class LLMConfig:
    use_langchain: bool = False  # Change to True for default LangChain
```

**Method 3: API Request (Programmatic)**
```bash
curl -X POST "http://localhost:8000/match?use_langchain=true"
```

---

## 🛠️ Current Status

### ✅ What's Working:
1. ✅ **agent4_llm_explainer.py** - Original Direct HTTP (fully working)
2. ✅ **agent4_factory.py** - Factory pattern (created, ready)
3. ✅ **agent4_langchain_explainer.py** - LangChain implementation (created, needs testing)
4. ✅ **pipeline.py** - Uses factory pattern (updated)
5. ✅ **api.py** - Per-request mode switching (updated)
6. ✅ **Frontend** - LangChain toggle UI (added)

### ⏳ What Needs to Be Done:
1. ❌ **Install LangChain dependencies**
   ```bash
   pip install langchain-ollama langchain-core
   ```

2. ❌ **Restart backend server**
   ```bash
   python src/api.py
   ```

3. ❌ **Test both modes**
   - Direct HTTP: Upload CV with toggle OFF
   - LangChain: Upload CV with toggle ON

---

## 🧪 Testing Commands

### Test 1: Check which mode is active
```bash
# Check logs when server starts
python src/api.py

# Should see:
# ✅ Agent 4 (Explainer) ready - LangChain: False  (Direct HTTP default)
```

### Test 2: Test Direct HTTP mode
```bash
# Run pytest
pytest tests/test_agent4_modes.py::test_direct_http_mode -v -s

# Or use frontend: Toggle AI Mode ON, LangChain OFF
```

### Test 3: Test LangChain mode
```bash
# Run pytest
pytest tests/test_agent4_modes.py::test_langchain_mode -v -s

# Or use frontend: Toggle both AI Mode ON and LangChain ON
```

### Test 4: Test factory fallback
```bash
pytest tests/test_agent4_modes.py::test_factory_fallback -v -s
```

---

## 🎨 Visual Summary

```
┌────────────────────────────────────────────────────────────┐
│               YOUR RECRUITER-PRO-AI SYSTEM                 │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  📁 src/agents/                                            │
│    ├── agent1_parser.py         (CV text extraction)      │
│    ├── agent2_extractor.py      (Data structuring)        │
│    ├── agent3_scorer.py         (Match scoring)           │
│    │                                                       │
│    ├── 🏭 agent4_factory.py      ← THE SWITCHER          │
│    │      └── Chooses which Agent 4 to use                │
│    │                                                       │
│    ├── ⚡ agent4_llm_explainer.py                         │
│    │      └── Fast Direct HTTP (default)                  │
│    │                                                       │
│    └── 🔗 agent4_langchain_explainer.py                   │
│           └── Advanced LangChain (optional)               │
│                                                            │
│  📁 src/                                                   │
│    ├── pipeline.py              (Orchestrates agents)     │
│    └── api.py                   (FastAPI endpoints)       │
│                                                            │
│  📁 frontend/                                              │
│    ├── app/page.tsx             (UI with toggles)         │
│    └── lib/api.ts               (API client)              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🚀 Next Steps

**IMMEDIATE ACTIONS:**

1. **Install dependencies:**
   ```bash
   cd c:\Users\DELL\Desktop\Recruiter-Pro-AI
   pip install langchain-ollama langchain-core
   ```

2. **Restart server:**
   ```bash
   python src/api.py
   ```

3. **Test in browser:**
   - Open frontend
   - Upload a CV
   - Try both modes:
     - ⚡ **Direct HTTP:** Fast, proven
     - 🔗 **LangChain:** Advanced, new features

4. **Check logs:**
   - Look for: `✅ Agent 4 (Explainer) ready - LangChain: False`
   - When toggling: `🔄 Switched to LangChain mode for this request`

---

## 💡 Key Takeaway

**Think of it like a car with two engines:**

- 🏎️ **Direct HTTP** = Gasoline engine (fast, efficient, proven)
- 🔋 **LangChain** = Electric engine (advanced features, cleaner code)
- 🏭 **Factory** = Transmission (switches between engines)

**You don't run engines separately - the car (pipeline) uses them automatically!**

The three files are **not scripts**, they are **components** of your Agent 4 system that work together seamlessly.
