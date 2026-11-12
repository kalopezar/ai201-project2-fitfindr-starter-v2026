# Path B — local run record

Captured 2026-11-11 at 21:35 local time from a clean checkout copy on Windows.
The documented startup command `python serve.py` started the service, `GET
/health` returned `{"status":"ok"}`, and a real `POST /ask` completed
successfully. It selected **Y2K Baby Tee — Butterfly Print**.

Request: `vintage graphic tee under $30`

Structured server log, pasted verbatim:

```json
{"event": "agent_request", "timestamp_utc": "2026-11-12T02:35:31.850Z", "request_id": "363565529c1d4941ae9a129c25f28a8c", "method": "POST", "path": "/ask", "status_code": 200, "duration_ms": 6386.23, "outcome": "success", "model": "gemini-3.5-flash-lite", "usage": {"model_calls": 2, "cache_hits": 0, "prompt_tokens": 631, "output_tokens": 198, "total_tokens": 829}}
```

## Environment observed for this run

- Python: 3.11.0
- Direct packages resolved in the environment: `python-dotenv 1.1.1`,
  `google-genai 1.75.0`, `mcp 1.30.0`, `Flask 3.1.3`, `gunicorn 23.0.0`.
  The allowed version bounds are in `requirements.txt`.
- Model: hosted API `gemini-3.5-flash-lite`; there are no local model files
  (0 bytes).
- Local data files: `data/listings.json` — 19,171 bytes;
  `data/wardrobe_schema.json` — 3,381 bytes.

The token counts above are the model usage metadata observed for this request.
The request log does not include provider billing data, so this record makes no
dollar-cost claim.
