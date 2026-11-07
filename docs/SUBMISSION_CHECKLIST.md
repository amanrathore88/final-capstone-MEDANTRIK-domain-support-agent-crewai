# Submission checklist (tick only on evidence)

- [ ] Exact official chosen domain name copied into submission form (likely `Chat Support System`).
- [ ] GitHub repo named e.g. `medantrik-assist-capstone`; repository is PUBLIC and opens in incognito.
- [ ] No Ola names/fixtures/copy-pasted code. Source is original, demo-only.
- [ ] One repo includes frontend + backend + dataset + 12 KB documents + tests + evaluation + docs.
- [ ] Python 3.11 environment setup and requirements/lock files tested from clean checkout.
- [ ] MOCK_LLM works without credentials after dependencies/model are installed.
- [ ] Dataset satisfies minimum quotas and printed counts exactly match README.
- [ ] Two Chroma collections, empirical threshold, retrieval precision/recall evidence recorded.
- [ ] Actual CrewAI kickoff and AutoGen review run (with captured proof).
- [ ] Per-session memory and guardrails tested, no raw phone leaks to JSONL.
- [ ] HTTP endpoints and WebSocket tested including disconnect.
- [ ] 15-case evaluation includes four scores + average; no fabricated perfect scores.
- [ ] Medically risky requests refuse diagnosis and trigger demo handoff.
- [ ] Frontend responsive with fully functional actions and real API data; no faux live support.
- [ ] Repo `.gitignore` excludes `.env`, local DB, local Chroma/model files, logs, caches, node_modules.
- [ ] README includes exact tested run commands, limitations, disclaimer, public fact sources and both-mode screenshots if used.
- [ ] `git status` clean, `git log -1` includes final code, Github link points to correct project.

## Minimal Git commands
```
git init
git add .
git commit -m "Build original Medantrik Assist support capstone"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/medantrik-assist-capstone.git
git push -u origin main
```
Create the **public** empty repository in GitHub first. Replace YOUR_USERNAME. Do not commit before ensuring secrets, runtime model/cache and private files are excluded. See README for verified dev commands; NEVER invent successful test outputs.
