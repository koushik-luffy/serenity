# Bits and Bytes Mental Health Support Prototype

This repository contains a mental-health support prototype with:

- a FastAPI backend for triage, crisis escalation, emergency-contact orchestration, queueing, and counselor actions
- a React + TypeScript + Tailwind frontend with separate user and counselor dashboards
- a Gemini-powered conversational assistant with server-side TTS
- a synthetic mental-health training dataset and a fine-tuned seed triage checkpoint

## Current Architecture

Backend:
- [triage_api/main.py](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/triage_api/main.py)
- [triage_api/service.py](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/triage_api/service.py)
- [triage_api/conversation.py](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/triage_api/conversation.py)

Frontend:
- [frontend/src/App.tsx](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/frontend/src/App.tsx)
- [frontend/src/pages/UserDashboard.tsx](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/frontend/src/pages/UserDashboard.tsx)
- [frontend/src/pages/CounselorDashboard.tsx](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/frontend/src/pages/CounselorDashboard.tsx)

Data and training:
- [data/realistic_triage_records.jsonl](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/data/realistic_triage_records.jsonl)
- [scripts/build_realistic_dataset.py](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/scripts/build_realistic_dataset.py)
- [scripts/train.py](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/scripts/train.py)
- [data/triage_tiny_model.pt](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/data/triage_tiny_model.pt)

## Features

- `POST /triage/analyze` returns severity, subtype, emergency flag, risk score, confidence, top indicators, and emergency routing metadata
- `POST /triage/summarize-history` builds a compact prior-session summary
- `POST /chat/respond` returns a warm Gemini-based reply and optional WAV audio as base64
- `POST /api/emergency-contacts` stores trusted contacts
- `GET /api/emergency-contacts/{user_id}` fetches trusted contacts
- `GET /api/queue` returns the counselor priority queue
- `GET /api/audit` returns audit activity
- `GET /api/alerts` returns simulated emergency alert deliveries
- `POST /api/queue/{session_id}/actions` lets counselors prioritize, start outreach, and resolve sessions

## Dashboards

The frontend has two separate pages:

- User dashboard: `#user`
- Counselor dashboard: `#counselor`

The user dashboard focuses on:
- live chat
- voice input
- server-generated voice playback
- triage-aware emotional support replies

The counselor dashboard focuses on:
- priority queue
- selected-session detail
- live alerts
- audit trail
- actions such as `prioritize`, `start_outreach`, and `resolve`

## Conversational AI

Chat is Gemini-only right now.

Required:
- `GEMINI_API_KEY`

Optional:
- `GEMINI_CHAT_MODEL` default: `gemini-2.5-flash`
- `GEMINI_TTS_MODEL` default: `gemini-2.5-flash-preview-tts`
- `GEMINI_TTS_VOICE` default: `Kore`

If `GEMINI_API_KEY` is missing, `/chat/respond` returns `503`.

The assistant prompt is tuned to:
- sound warmer and less generic
- reflect specific details from the user’s message
- shift into direct crisis-support language when triage indicates danger

## Triage Model

The triage system has two layers:

1. A trained transformer classifier for severity, subtype, emergency flag, and risk
2. A rule-based safe-fail layer that can override unsafe or under-confident model outputs

The repo now includes a fine-tuned seed checkpoint:
- `TRIAGE_ENCODER_NAME=prajjwal1/bert-tiny`
- `TRIAGE_MODEL_WEIGHTS=data/triage_tiny_model.pt`

If `TRIAGE_MODEL_WEIGHTS` is not set, the backend falls back to the heuristic classifier so the app still runs.

## Mental-Health Dataset

The synthetic dataset in [data/realistic_triage_records.jsonl](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/data/realistic_triage_records.jsonl) currently contains 2100 mental-health-focused records generated from [scripts/build_realistic_dataset.py](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/scripts/build_realistic_dataset.py).

Coverage includes:
- low-level stress and emotional fragility
- panic and anxiety
- hopelessness and depressive flattening
- indirect suicidal ideation
- self-harm
- overdose
- abuse and immediate danger
- violent intent and harm-to-others language

Important:
- this is synthetic training data, not clinician-labeled production data
- it is useful for a prototype and demo
- it should not be treated as clinically validated

## Crisis and Violence Handling

The rule layer in [triage_api/rules.py](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/triage_api/rules.py) and [triage_api/service.py](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/triage_api/service.py) escalates both direct and indirect crisis language.

Examples that are treated as high risk include:
- “everyone would be better off without me”
- “I wish I could disappear”
- “I might snap and hurt him”
- “I want to kill someone”
- “I want to kidnap someone”

When harm-to-others language is detected, the system routes the case as:
- severity: `high_crisis`
- subtype: `abuse_violence`
- emergency: `true`

That means it can appear in the counselor priority queue and trigger emergency workflow behavior.

## Environment Setup

Create a file named [`.env`](C:/Users/KOUSHIK/projects/Bits%20and%20Bytes/.env) in the project root:

```env
GEMINI_API_KEY=your_actual_key_here
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_TTS_MODEL=gemini-2.5-flash-preview-tts
GEMINI_TTS_VOICE=Kore
TRIAGE_ENCODER_NAME=prajjwal1/bert-tiny
TRIAGE_MODEL_WEIGHTS=data/triage_tiny_model.pt
```

Do not wrap the key in quotes.

## Backend Run

```bash
pip install -r requirements.txt
uvicorn triage_api.main:app --reload
```

## Frontend Run

```bash
cd frontend
npm install
npm run dev
```

Then open the Vite app and use:
- `#user` for the user dashboard
- `#counselor` for the counselor dashboard

## Retraining the Triage Model

Regenerate the dataset:

```bash
python scripts/build_realistic_dataset.py
```

Train a new checkpoint:

```bash
python scripts/train.py --data data/realistic_triage_records.jsonl --output data/triage_tiny_model.pt --encoder-name prajjwal1/bert-tiny --epochs 1 --batch-size 8 --learning-rate 3e-5
```

Notes:
- the original larger DeBERTa path is heavier and may be harder to run in constrained environments
- the smaller `prajjwal1/bert-tiny` checkpoint is included because it is practical for local prototype training

## Verification

Run backend tests:

```bash
python -m unittest discover -s tests -v
```

Current status:
- backend tests pass
- the included fine-tuned checkpoint loads successfully with cache-only model loading

