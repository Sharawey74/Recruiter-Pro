# 🚀 QUICK START - TEST THE APP NOW!

## ✅ Ollama is OPTIONAL - App loads 100 jobs for fast testing!

---

## 🎯 FASTEST WAY TO TEST (1 COMMAND)

### Option 1: Automated (Recommended)
```powershell
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI
.\Run.ps1
```

**What it does:**
- ✅ Starts FastAPI on port 8000
- ✅ Starts Next.js on port 3000
- ✅ Loads only 100 jobs (fast!)
- ✅ No Ollama needed (toggle it later)

**Wait for:**
```
✓ FastAPI Server Ready on port 8000
✓ Next.js Frontend Ready on port 3000
Access the app at: http://localhost:3000
```

---

### Option 2: Manual (2 Terminals)

**Terminal 1 - Backend:**
```powershell
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI
python -m uvicorn src.api:app --reload
```

**Terminal 2 - Frontend:**
```powershell
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI\frontend
npm run dev
```

---

## 🎉 TEST IT!

### 1. Open Browser
http://localhost:3000/upload

### 2. Look for the Toggle
You'll see a checkbox that says:
```
□ Enable AI Explanations (Ollama LLM)
✓ Fast mode - Rule-based matching only (no Ollama needed)
```

### 3. Keep it UNCHECKED (Fast Mode)
This means:
- ✅ No Ollama required
- ✅ Works immediately
- ✅ Fast (2-3 seconds for 100 jobs)
- ✅ No timeout errors

### 4. Upload a CV
- Drag and drop any PDF or DOCX file
- Or click to browse

### 5. Click "Match CVs"

### 6. Should Work! ✅
- Processing completes in 2-3 seconds
- No "failed to process CVs" error
- Shows match results from 100 jobs

---

## 📊 WHAT YOU'LL SEE

### Terminal Output (Good):
```
INFO: Loaded 100 jobs from data\json\jobs.json (limited for testing)
INFO: Matching CV: Resume.pdf (top_k=10, explain=False, use_llm=False)
INFO: ⚙️ LLM disabled - using rule-based explanations only
INFO: Running pipeline against 100 jobs...
INFO: Matching complete. Found 10 matches.
```

### Browser (Good):
- Upload successful toast ✅
- Match results displayed
- Job cards with scores
- Statistics summary

---

## ⚡ KEY POINTS

1. **Loads only 100 jobs** (instead of 3000) for fast testing
2. **Default is Fast Mode** (no Ollama)
3. **Toggle is on Upload page**
4. **OFF = Fast mode** (2-3s, no Ollama)
5. **ON = AI mode** (20-30s, needs Ollama)

---

## ✅ SUCCESS CHECKLIST

- [ ] Ran `.\Run.ps1` or started services manually
- [ ] FastAPI shows "Loaded 100 jobs"
- [ ] Next.js shows "Ready in 3-5s"
- [ ] Browser shows upload page
- [ ] Toggle is visible and **OFF**
- [ ] Uploaded a CV
- [ ] Clicked "Match CVs"
- [ ] Got results in 2-3 seconds
- [ ] No errors!

**If all checkboxes are ✅, IT WORKS!** 🎉
