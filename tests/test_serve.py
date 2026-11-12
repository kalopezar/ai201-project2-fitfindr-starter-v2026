import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import serve


class ServeCriteriaTests(unittest.TestCase):
    def setUp(self):
        self.client = serve.app.test_client()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "agent_requests.jsonl"
        self.log_path_patch = patch.object(serve, "LOG_PATH", self.log_path)
        self.log_path_patch.start()

    def tearDown(self):
        self.log_path_patch.stop()
        self.temp_dir.cleanup()

    def log_lines(self):
        return self.log_path.read_text(encoding="utf-8").splitlines()

    def log_records(self):
        return [json.loads(line) for line in self.log_lines()]

    @staticmethod
    def successful_session():
        return {
            "error": None,
            "selected_item": {
                "id": "lst_test",
                "title": "Test listing",
                "price": 18.0,
                "platform": "depop",
            },
            "outfit_suggestion": "Test outfit",
            "fit_card": "Test caption",
        }

    def test_criterion_1_five_successful_runs_have_required_fields(self):
        with patch("builtins.print") as print_mock:
            with patch.object(
                serve,
                "run_agent",
                side_effect=[self.successful_session() for _ in range(5)],
            ):
                responses = [
                    self.client.post("/ask", json={"query": f"query {index}"})
                    for index in range(5)
                ]

        self.assertTrue(all(response.status_code == 200 for response in responses))
        print_mock.assert_not_called()
        lines = self.log_lines()
        records = [json.loads(line) for line in lines]
        self.assertEqual(len(lines), 5)
        self.assertEqual(len(records), 5)
        for record in records:
            self.assertTrue(record["timestamp"].endswith("Z"))
            self.assertTrue(record["request_id"])
            self.assertIsInstance(record["input"]["query"], str)
            self.assertIsInstance(record["output"], dict)
            self.assertIsInstance(record["duration_ms"], (int, float))
            self.assertGreaterEqual(record["duration_ms"], 0)
            self.assertEqual(record["status_code"], 200)
            self.assertEqual(record["outcome"], "success")
            for name in (
                "model_calls",
                "prompt_tokens",
                "output_tokens",
                "total_tokens",
            ):
                self.assertIsInstance(record["usage"][name], int)
                self.assertGreaterEqual(record["usage"][name], 0)

    def test_criterion_2_three_failure_types_each_leave_error_record(self):
        rejected = self.client.post("/ask", json={"query": "   "})

        agent_error = {
            "error": "Model unavailable",
            "selected_item": None,
            "outfit_suggestion": None,
            "fit_card": None,
        }
        with patch.object(serve, "run_agent", return_value=agent_error):
            returned_failure = self.client.post(
                "/ask", json={"query": "returned failure"}
            )

        with patch.object(
            serve, "run_agent", side_effect=RuntimeError("test exception")
        ):
            raised_failure = self.client.post(
                "/ask", json={"query": "raised failure"}
            )

        self.assertEqual(
            [rejected.status_code, returned_failure.status_code, raised_failure.status_code],
            [400, 200, 500],
        )
        records = self.log_records()
        self.assertEqual(len(records), 3)
        self.assertEqual(
            [record["outcome"] for record in records],
            ["invalid_query", "agent_error", "server_error"],
        )
        self.assertTrue(
            all(isinstance(record["output"]["error"], str) and record["output"]["error"]
                for record in records)
        )

    def test_criterion_3_five_distinct_requests_append_in_order(self):
        queries = [f"distinct query {index}" for index in range(5)]
        self.assertFalse(self.log_path.exists())
        with patch.object(
            serve,
            "run_agent",
            side_effect=[self.successful_session() for _ in queries],
        ):
            responses = [
                self.client.post("/ask", json={"query": query})
                for query in queries
            ]

        self.assertTrue(all(response.status_code == 200 for response in responses))
        lines = self.log_lines()
        records = [json.loads(line) for line in lines]
        self.assertEqual(len(lines), 5)
        self.assertEqual([record["input"]["query"] for record in records], queries)

    def test_criterion_4_five_records_keep_summaries_and_omit_payloads(self):
        sessions = []
        requests = []
        sentinels = []
        for index in range(5):
            wardrobe_secret = f"wardrobe-secret-{index}"
            outfit_secret = f"outfit-secret-{index}"
            caption_secret = f"caption-secret-{index}"
            sentinels.extend((wardrobe_secret, outfit_secret, caption_secret))
            requests.append({
                "query": f"privacy query {index}",
                "wardrobe": {
                    "items": [{"name": wardrobe_secret}] * (index + 1),
                },
            })
            sessions.append({
                "error": None,
                "selected_item": {
                    "id": f"lst_{index}",
                    "title": f"Listing {index}",
                    "price": 10 + index,
                    "platform": "depop",
                },
                "outfit_suggestion": outfit_secret,
                "fit_card": caption_secret,
            })

        with patch.object(serve, "run_agent", side_effect=sessions):
            responses = [
                self.client.post("/ask", json=payload) for payload in requests
            ]

        self.assertTrue(all(response.status_code == 200 for response in responses))
        lines = self.log_lines()
        records = [json.loads(line) for line in lines]
        self.assertEqual(len(records), 5)
        for index, record in enumerate(records):
            self.assertEqual(record["input"]["wardrobe_item_count"], index + 1)
            self.assertEqual(record["output"]["selected_item"]["id"], f"lst_{index}")
        self.assertEqual(
            sum(sentinel in line for sentinel in sentinels for line in lines), 0
        )


if __name__ == "__main__":
    unittest.main()
