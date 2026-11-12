import contextlib
import io
import json
import unittest
from unittest.mock import patch

import serve


class ServeLoggingTests(unittest.TestCase):
    def setUp(self):
        self.client = serve.app.test_client()
        self.output = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.output)
        self.redirect.__enter__()

    def tearDown(self):
        self.redirect.__exit__(None, None, None)

    def log_records(self):
        return [
            json.loads(line)
            for line in self.output.getvalue().splitlines()
            if line.startswith("{")
        ]

    def test_successful_request_returns_agent_session_and_logs_usage(self):
        session = {"error": None, "selected_item": {"id": "lst_002"}}
        with patch.object(serve, "run_agent", return_value=session):
            response = self.client.post("/ask", json={"query": "test search"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), session)
        [record] = self.log_records()
        self.assertEqual(record["event"], "agent_request")
        self.assertEqual(record["status_code"], 200)
        self.assertEqual(record["outcome"], "success")
        self.assertGreaterEqual(record["duration_ms"], 0)
        self.assertEqual(
            set(record["usage"]),
            {
                "model_calls",
                "cache_hits",
                "prompt_tokens",
                "output_tokens",
                "total_tokens",
            },
        )
        self.assertNotIn("test search", json.dumps(record))


if __name__ == "__main__":
    unittest.main()
