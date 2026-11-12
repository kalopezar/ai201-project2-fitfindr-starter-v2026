# Path B — local run record

Captured 2026-11-11 at 22:04 local time on Windows. The documented startup
command `python serve.py` started the service, `GET /health` returned
`{"status":"ok"}`, and a real `POST /ask` completed successfully. It selected
**Y2K Baby Tee — Butterfly Print**.

Request: `vintage graphic tee under $30`

The server appended this JSONL record to `results/agent_requests.jsonl`:

```json
{"event": "agent_request", "timestamp": "2026-11-12T03:04:01.356Z", "request_id": "7df10dacb2f74b4a8012f7d2e036379e", "method": "POST", "path": "/ask", "status_code": 200, "duration_ms": 2406.31, "outcome": "success", "model_id": "gemini-3.5-flash-lite", "input": {"query": "vintage graphic tee under $30", "wardrobe_item_count": 10}, "output": {"error": null, "selected_item": {"id": "lst_002", "title": "Y2K Baby Tee — Butterfly Print", "price": 18.0, "platform": "depop"}, "has_outfit_suggestion": true, "has_fit_card": true}, "usage": {"model_calls": 0, "cache_hits": 2, "prompt_tokens": 0, "output_tokens": 0, "total_tokens": 0}}
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

Both model responses were served from cache, so this run made no model calls
and recorded zero newly used tokens. The log does not include provider billing
data, so this record makes no dollar-cost claim. The live JSONL file is
git-ignored because it contains search queries; this committed copy is a run
record for inspection.
