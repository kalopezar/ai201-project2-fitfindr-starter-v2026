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

    def test_invalid_queries_are_rejected_and_logged(self):
        for payload in ({}, {"query": 42}, []):
            with self.subTest(payload=payload):
                response = self.client.post("/ask", json=payload)
                self.assertEqual(response.status_code, 400)

        records = self.log_records()
        self.assertEqual(len(records), 3)
        self.assertTrue(
            all(
                record["status_code"] == 400
                and record["outcome"] == "invalid_query"
                for record in records
            )
        )

    def test_agent_exception_returns_and_logs_server_error(self):
        with patch.object(serve, "run_agent", side_effect=ValueError("test failure")):
            response = self.client.post("/ask", json={"query": "test search"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"error": "ValueError: test failure"})
        [record] = self.log_records()
        self.assertEqual(record["status_code"], 500)
        self.assertEqual(record["outcome"], "server_error")
        self.assertEqual(record["error_type"], "ValueError")
        self.assertNotIn("test search", json.dumps(record))


if __name__ == "__main__":
    unittest.main()
