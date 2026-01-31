# 🚀 HOW TO START THE APPLICATION - STEP BY STEP GUIDE

## ⚠️ IMPORTANT: Why You Saw "Index of /" Error

**Problem:** The "Index of /" directory listing appears when:
1. Next.js dev server crashes or fails to start
2. Port 3000 is occupied by another service (like a web server showing file listing)
3. Build errors prevent the app from loading

**Solution:** Follow the steps below carefully.

---

## 📋 PREREQUISITES CHECK

Before starting, verify you have:

### 1. Required Software
```powershell
# Check Node.js (need v18+)
node --version
# Should show: v18.x.x or higher

# Check npm
npm --version
# Should show: 9.x.x or higher

# Check Python (need 3.8+)
python --version
# Should show: Python 3.8+ or higher

# Check if ports are free
Test-NetConnection localhost -Port 3000
Test-NetConnection localhost -Port 8000
Test-NetConnection localhost -Port 11500
```

### 2. Kill Any Existing Processes
```powershell
# Stop all Node.js processes
Get-Process | Where-Object { $_.ProcessName -match "node" } | Stop-Process -Force

# Stop uvicorn (FastAPI)
Get-Process | Where-Object { $_.ProcessName -match "python" } | Stop-Process -Force

# Stop Ollama
Get-Process | Where-Object { $_.ProcessName -match "ollama" } | Stop-Process -Force
```

---

## 🎯 METHOD 1: MANUAL STEP-BY-STEP (RECOMMENDED FOR FIRST TIME)

### Step 1: Open 3 Separate PowerShell Terminals

**Terminal 1 - Ollama:**
```powershell
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI
ollama serve
```
Wait until you see: `Listening on 127.0.0.1:11500`

**Terminal 2 - FastAPI Backend:**
```powershell
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```
Wait until you see:
```
✅ API Server Ready!
📖 API Docs: http://localhost:8000/docs
Uvicorn running on http://0.0.0.0:8000
```

**Terminal 3 - Next.js Frontend:**
```powershell
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI\frontend

# First time? Install dependencies
npm install

# Clean cache if issues
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue

# Start dev server
npm run dev
```
Wait until you see:
```
✓ Ready in 3-5s
Local: http://localhost:3000
```

### Step 2: Verify Services

**Check Ollama (Terminal 1):**
```
✓ Should show "Listening on 127.0.0.1:11500"
```

**Check FastAPI (Terminal 2):**
```
✓ Should show:
  - "✅ Loaded 3000 jobs"
  - "✅ API Server Ready!"
  - "Uvicorn running on http://0.0.0.0:8000"
```

**Check Next.js (Terminal 3):**
```
✓ Should show:
  - "✓ Ready in 3-5s"
  - "Local: http://localhost:3000"
```

### Step 3: Test the App

1. Open browser: http://localhost:3000
2. You should see the **Dashboard page** (not "Index of /")
3. Test API: http://localhost:8000/docs

---

## 🚀 METHOD 2: AUTOMATED LAUNCHER (Use After First Successful Manual Start)

### Using Run.ps1 (Updated Version)

**Single Command:**
```powershell
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI
.\Run.ps1
```

**What it does:**
1. Starts Ollama on port 11500
2. Starts FastAPI on port 8000 (shows API startup logs)
3. Starts Next.js on port 3000 (shows compilation status)
4. Monitors all services

**To Stop:**
- Press `Ctrl+C` in the terminal
- All services will shut down gracefully

---

## 🔧 TROUBLESHOOTING

### Issue 1: "Index of /" Showing
**Cause:** Next.js dev server not running or crashed

**Solution:**
```powershell
# Kill all node processes
Get-Process | Where-Object { $_.ProcessName -match "node" } | Stop-Process -Force

# Go to frontend folder
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI\frontend

# Clean cache
Remove-Item -Recurse -Force .next

# Reinstall if needed
npm install

# Start fresh
npm run dev
```

### Issue 2: Port Already in Use
**Error:** `Port 3000 is already in use`

**Solution:**
```powershell
# Find process using port 3000
netstat -ano | findstr :3000

# Kill it (replace PID with the number from above)
taskkill /PID <PID> /F

# Or kill all node processes
Get-Process | Where-Object { $_.ProcessName -match "node" } | Stop-Process -Force
```

### Issue 3: Sonner Import Error
**Error:** `Cannot find module 'sonner'`

**Solution:**
```powershell
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI\frontend
npm install sonner --save
```

### Issue 4: Backend Not Starting
**Error:** FastAPI fails to start

**Solution:**
```powershell
# Check if required files exist
Test-Path "C:\Users\DELL\Desktop\Recruiter-Pro-AI\data\json\jobs.json"
Test-Path "C:\Users\DELL\Desktop\Recruiter-Pro-AI\models\production\ats_model.joblib"

# Try starting manually to see full error
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI
python -m uvicorn src.api:app --reload
```

### Issue 5: Compilation Errors
**Error:** TypeScript errors in console

**Solution:**
```powershell
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI\frontend

# Clean everything
Remove-Item -Recurse -Force .next
Remove-Item -Recurse -Force node_modules

# Fresh install
npm install

# Try building
npm run build

# If build succeeds, start dev server
npm run dev
```

---

## 📊 EXPECTED STARTUP SEQUENCE

### Timeline (Normal Startup)
```
0:00  - Ollama starts
0:03  - Ollama ready on port 11500 ✓
0:03  - FastAPI starts loading
0:05  - ML model loaded ✓
0:07  - 3000 jobs loaded ✓
0:09  - Database ready ✓
0:10  - FastAPI ready on port 8000 ✓
0:10  - Next.js starts
0:14  - Next.js ready on port 3000 ✓

Total: ~15 seconds
```

---

## ✅ SUCCESS CHECKLIST

After starting, you should see:

### Terminal 1 (Ollama):
```
✓ Listening on 127.0.0.1:11500
```

### Terminal 2 (FastAPI):
```
✓ 🚀 Initializing 4-Agent Pipeline...
✓ ✅ Agent 1 (Parser) ready
✓ ✅ Agent 2 (Extractor) ready
✓ ✅ Agent 3 (Scorer) ready
✓ ✅ Agent 4 (Explainer) ready
✓ 🎉 Pipeline initialization complete!
✓ ✅ Loaded 3000 jobs
✓ ✅ API Server Ready!
✓ Uvicorn running on http://0.0.0.0:8000
```

### Terminal 3 (Next.js):
```
✓ ▲ Next.js 14.2.3
✓ - Local: http://localhost:3000
✓ ✓ Ready in 3.8s
```

### Browser (http://localhost:3000):
```
✓ Shows "AI Resume Matcher" Dashboard
✓ Sidebar visible with 4 pages
✓ API status shows GREEN dot
✓ No "Index of /" error
```

---

## 🔍 HOW TO VERIFY EVERYTHING WORKS

### Test 1: Health Check
```powershell
# Test backend
curl http://localhost:8000/health

# Should return:
# {"status":"healthy"}
```

### Test 2: Jobs API
```powershell
curl http://localhost:8000/jobs?limit=1

# Should return JSON with job data
```

### Test 3: Frontend Pages
Visit in browser:
- http://localhost:3000 (Dashboard) ✓
- http://localhost:3000/upload (Upload CVs) ✓
- http://localhost:3000/results (Match History) ✓
- http://localhost:3000/jobs (Job Database) ✓

### Test 4: API Documentation
- http://localhost:8000/docs (Swagger UI) ✓

---

## 📝 QUICK REFERENCE COMMANDS

### Start Services (Manual)
```powershell
# Terminal 1
ollama serve

# Terminal 2
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI\frontend
npm run dev
```

### Stop Services
```powershell
# In each terminal: Ctrl+C

# Or kill all at once:
Get-Process | Where-Object { $_.ProcessName -match "ollama|python|node" } | Stop-Process -Force
```

### Clean Start (if problems)
```powershell
# Clean Next.js cache
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI\frontend
Remove-Item -Recurse -Force .next

# Reinstall dependencies
npm install

# Start fresh
npm run dev
```

---

## 🎯 COMMON MISTAKES TO AVOID

1. ❌ **Don't navigate away from terminal** - Keep terminals open
2. ❌ **Don't close terminals** - Services will stop
3. ❌ **Don't start multiple instances** - Check if already running
4. ❌ **Don't skip npm install** - Always install dependencies first time
5. ❌ **Don't use old cache** - Clean .next folder if issues

✅ **Do wait for "Ready" message** before testing
✅ **Do check all 3 services are running** before accessing app
✅ **Do use Ctrl+C to stop gracefully**

---

## 🆘 STILL NOT WORKING?

### Nuclear Option (Complete Reset)
```powershell
# 1. Stop everything
Get-Process | Where-Object { $_.ProcessName -match "ollama|python|node" } | Stop-Process -Force

# 2. Clean frontend
cd C:\Users\DELL\Desktop\Recruiter-Pro-AI\frontend
Remove-Item -Recurse -Force .next
Remove-Item -Recurse -Force node_modules
npm install

# 3. Start services one by one and watch for errors
# Follow Method 1 above
```

---

## 📞 SUPPORT CHECKLIST

If you still have issues, gather this info:

1. **Node.js version:** `node --version`
2. **Python version:** `python --version`
3. **Port status:** `netstat -ano | findstr ":3000\|:8000\|:11500"`
4. **Error messages:** Copy from terminals
5. **Browser console:** Press F12, check for errors

---

**Last Updated:** 2026-01-30  
**Status:** ✅ Working (after following steps)  
**Support:** Check error logs in each terminal
