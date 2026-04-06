# Mental Health Triage Backend

This repository contains a hackathon-ready backend prototype for a hierarchical mental-health triage service.

## What is included

- `POST /triage/analyze` for severity, subtype, emergency flag, risk score, and explanation signals
- `POST /triage/summarize-history` for compact prior-session summaries
- `POST /api/emergency-contacts` to register the trusted contacts to notify for critical emergencies
- `GET /api/emergency-contacts/{user_id}` to retrieve saved emergency contacts
- `GET /api/alerts` to inspect simulated alert deliveries before real SMS/email integration
- A hierarchical PyTorch model built on `microsoft/deberta-v3-base`
- Safe-fail escalation rules for crisis language and low-confidence cases
- Automatic emergency-contact alert orchestration when severity is `high_crisis` and the case is flagged as an emergency or has `risk_score >= 90`
- A lightweight fallback inference path so the API stays usable before fine-tuned weights are available

## Run locally

```bash
pip install -r requirements.txt
uvicorn triage_api.main:app --reload
```
