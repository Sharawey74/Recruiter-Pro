# Deployment

Next.js on **Vercel**, FastAPI on **Railway**, SQLite on a Railway **volume**.

Two measurements drove those choices, taken against the running app on
17 Aug 2026:

| | |
|---|--:|
| Memory after startup | **215 MB** |
| Cold start | **21.9 s** |

215 MB fits any free tier. The 21.9 s is what ruled options out.

**Netlify was rejected for the backend.** It runs serverless functions, which
time out at 10 s on the free plan and 26 s at most. This is a long-running
process holding an 800-role corpus and a joblib model in memory — the cold start
alone exceeds the ceiling. Netlify remains a perfectly good host for the
frontend if you prefer it to Vercel.

**Render's free tier was rejected.** It sleeps after 15 minutes of inactivity.
With a 21.9 s cold start on top of container wake, the first visitor after a
quiet hour waits about half a minute at a blank page and concludes the app is
broken. Railway does not sleep. For a link someone may open once, "it is always
there" is the whole point.

---

## 1 · Railway — the API

### Create the service

Point Railway at the repository root. `railway.json` supplies the build and
deploy configuration:

```
startCommand      python -m uvicorn src.api:app --host 0.0.0.0 --port $PORT --workers 1
healthcheckPath   /health
```

**One worker, deliberately.** Each worker loads its own copy of the corpus and
the model — 215 MB apiece — and the workload is one CPU-bound request at a time.
Two workers doubles the memory to serve a queue of one.

`/health` is the health check because it reports what actually loaded: the
corpus size and whether the ML model is present. A process that is up but
serving an empty corpus fails it, which is the point.

### Attach a volume

**Without this, every deploy wipes the database.** Railway's filesystem is
ephemeral, and the database now holds three things you want to keep: match
history, the daily LLM quota counter, and — since the corpus became writable —
the jobs themselves.

Mount a volume at `/data`, then set `DATABASE_PATH=/data/match_history.db`.

On first boot against an empty volume the app seeds the `jobs` table from
`data/json/jobs.json`. That seed only runs into an empty table, so redeploys
never overwrite a job you have edited.

### Environment variables

| Variable | Value | Why |
|---|---|---|
| `CORS_ORIGINS` | `https://<app>.vercel.app` | Exact match, no trailing slash. This is a real control, not a formality |
| `DATABASE_PATH` | `/data/match_history.db` | Must point inside the mounted volume |
| `TRUST_PROXY_HEADERS` | `true` | **Required.** See below |
| `RATE_LIMIT_ENABLED` | `true` | |
| `LLM_PROVIDER` | `rule_based` or `openrouter` | `rule_based` costs nothing and adds no latency |
| `OPENROUTER_API_KEY` | *(secret)* | Only if the provider is `openrouter`. Railway variables, never the repository |
| `LLM_DAILY_QUOTA` | `200` | Real money on a public URL |
| `ENV` | `production` | |

`API_HOST` and `API_PORT` are not needed — the start command sets both, and
`$PORT` is injected by Railway.

**On `TRUST_PROXY_HEADERS`.** Rate limits are charged per client address. Behind
Railway's proxy the socket address is the *proxy's*, so without this every
visitor shares one bucket and ordinary traffic starts collecting 429s while an
attacker is no more limited than before. It is off by default because the
opposite mistake is worse: trusting `X-Forwarded-For` with nothing in front lets
any client invent an address per request. Turn it on **only** because Railway is
in front.

---

## 2 · Vercel — the frontend

Root directory `frontend`. Framework preset Next.js; everything else is default.

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<api>.up.railway.app` |

**Set this before the first build.** `NEXT_PUBLIC_*` is inlined by
`next build`, not read at runtime — deploy without it and the frontend ships
with `http://localhost:8000` compiled in. Changing it later requires a rebuild,
not a restart.

**Preview deployments get generated URLs** that will not match `CORS_ORIGINS`,
so previews cannot reach the API. Either add each preview origin, or accept that
only production talks to the backend. Do not be tempted by `*` — the CORS
specification forbids it alongside credentials, so browsers reject the response
outright and every call fails.

---

## 3 · Order

Railway first. Vercel needs the API's URL at build time, and Railway needs
Vercel's origin for CORS — so:

1. Deploy Railway with `CORS_ORIGINS` set to a placeholder.
2. Note the generated API URL.
3. Deploy Vercel with `NEXT_PUBLIC_API_URL` pointing at it.
4. Update `CORS_ORIGINS` on Railway to the real Vercel origin. This restarts the
   API, which is fine — it does not rebuild.

---

## 4 · Verify

```bash
curl https://<api>.up.railway.app/health
```

```json
{
  "status": "healthy",
  "components": {
    "agents_loaded": true,
    "jobs_loaded": 800,
    "ml_model_loaded": true,
    "database_ready": true,
    "explanation_provider": "rule_based",
    "llm_enabled": true
  }
}
```

Read it field by field — each one fails differently:

| Field | If it is wrong |
|---|---|
| `jobs_loaded` | Not 800: the volume is mounted but `DATABASE_PATH` points outside it, or the seed failed |
| `ml_model_loaded` | `false`: the joblib artifacts did not ship. Scoring still works, rule-based only, and the sidebar says so |
| `database_ready` | `false`: no volume, or `DATABASE_PATH` points somewhere unwritable |
| `explanation_provider` | **The provider that will actually answer.** Must match your `LLM_PROVIDER`. If you set `openrouter` and this says `rule_based`, the key is missing or the provider failed to construct — the app is working and quietly not using your key |

That last row is the whole reason the field exists. It read `ollama_enabled`
until this deployment was prepared, reporting a config flag rather than a
provider, so an instance running `rule_based` announced Ollama — a provider
that cannot run on this host at all.

Then, in the browser, confirm the frontend loads figures on the landing page —
those come from `GET /stats`, so they are an end-to-end proof that CORS, the
API URL and the corpus are all correct at once.

### Measuring performance after deployment

Report end-to-end latency **separately** from `processing_time`. They answer
different questions, and conflating them makes both meaningless:

| | Measures |
|---|---|
| `processing_time` in the response | Server-side compute — the 0.74 s figure |
| Wall clock from the browser | + TLS + network + any cold start |

Load testing with k6 or Locust goes against the deployed API. Vercel Analytics
covers real-user frontend vitals. If you add an uptime pinger, point it at
`/health`.

---

## Known costs

**The production image installs the training and test stacks.** `xgboost`,
`matplotlib`, `seaborn`, `pytest`, `black`, `ruff` and `mypy` are in
`requirements.txt` and none of them are imported by the API. This is the
deliberate cost of one dependency file instead of three; it affects build time
and image size, not correctness. The runtime section of `requirements.txt` is
marked, and splitting it back out is the fix if builds drag.

Four `langchain*` pins used to be in that list too and are gone as of
`332471f` — the provider that needed them wrapped `ChatOllama` to reach the
same Ollama server the `ollama` provider reaches directly, and Ollama is not
reachable from Railway in any case. That is the single largest thing already
removed from this build.

**There is no authentication.** `POST`, `PUT` and `DELETE /jobs` are open on a
public URL. They are rate limited per IP, which bounds the damage but is not a
substitute for auth — anyone who finds them can edit the corpus. This was a
deliberate scope decision, and it is the thing to close first if the deployment
becomes more than a demonstration.
