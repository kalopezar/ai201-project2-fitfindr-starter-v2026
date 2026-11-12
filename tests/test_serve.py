import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import serve


class ServeLoggingTests(unittest.TestCase):
    def setUp(self):
        self.client = serve.app.test_client()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "agent_requests.jsonl"
        self.log_path_patch = patch.object(serve, "LOG_PATH", self.log_path)
        self.log_path_patch.start()

    def tearDown(self):
        self.log_path_patch.stop()
        self.temp_dir.cleanup()

    def log_records(self):
        return [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").splitlines()
        ]

    def test_successful_request_appends_structured_record_to_file(self):
        session = {
            "error": None,
            "selected_item": {
                "id": "lst_002",
                "title": "Test listing",
                "price": 18.0,
                "platform": "depop",
            },
            "outfit_suggestion": "Private generated text",
            "fit_card": "Private generated caption",
        }
        with patch("builtins.print") as print_mock:
            with patch.object(serve, "run_agent", return_value=session):
                response = self.client.post(
                    "/ask",
                    json={
                        "query": "test search",
                        "wardrobe": {"items": [{"name": "Private wardrobe item"}]},
                    },
                )

        self.assertEqual(response.status_code, 200)
        print_mock.assert_not_called()
        self.assertEqual(response.get_json(), session)
        [record] = self.log_records()
        self.assertEqual(record["event"], "agent_request")
        self.assertEqual(record["status_code"], 200)
        self.assertEqual(record["outcome"], "success")
        self.assertEqual(record["model_id"], serve.config.MODEL)
        self.assertTrue(record["timestamp"].endswith("Z"))
        self.assertGreaterEqual(record["duration_ms"], 0)
        self.assertIn("timestamp", record)
        self.assertEqual(
            record["input"],
            {"query": "test search", "wardrobe_item_count": 1},
        )
        self.assertEqual(
            record["output"],
            {
                "error": None,
                "selected_item": {
                    "id": "lst_002",
                    "title": "Test listing",
                    "price": 18.0,
                    "platform": "depop",
                },
                "has_outfit_suggestion": True,
                "has_fit_card": True,
            },
        )
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
        contents = self.log_path.read_text(encoding="utf-8")
        self.assertEqual(len(contents.splitlines()), 1)
        self.assertNotIn("Private wardrobe item", contents)
        self.assertNotIn("Private generated text", contents)
        self.assertNotIn("Private generated caption", contents)

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
                and record["output"]["error"]
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
        self.assertEqual(record["output"], {"error": "ValueError: test failure"})

    def test_records_append_as_separate_json_lines(self):
        for query in ("first", "second"):
            with patch.object(serve, "run_agent", return_value={"error": "no match"}):
                response = self.client.post("/ask", json={"query": query})
            self.assertEqual(response.status_code, 200)

        records = self.log_records()
        self.assertEqual(
            [record["input"]["query"] for record in records], ["first", "second"]
        )
        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
