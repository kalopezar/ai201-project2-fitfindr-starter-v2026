# Capstone test run log — three runs

Each run used a separate fresh `git clone` of the repository, the configured
Python 3.11 virtual environment, and the local `.env` copied into the ignored
clone. For each clone I ran
`python -m unittest discover -s tests -v`, then started `python serve.py` and
requested `/health`. The four tests directly exercise criteria 1–4 with
isolated temporary JSONL files; criterion 5 is an actual server process and
HTTP request. The startup ports differed to keep runs isolated.

## Run 1

Automated criteria 1–4:

```text
test_criterion_1_five_successful_runs_have_required_fields (test_serve.ServeCriteriaTests.test_criterion_1_five_successful_runs_have_required_fields) ... ok
test_criterion_2_three_failure_types_each_leave_error_record (test_serve.ServeCriteriaTests.test_criterion_2_three_failure_types_each_leave_error_record) ... ok
test_criterion_3_five_distinct_requests_append_in_order (test_serve.ServeCriteriaTests.test_criterion_3_five_distinct_requests_append_in_order) ... ok
test_criterion_4_five_records_keep_summaries_and_omit_payloads (test_serve.ServeCriteriaTests.test_criterion_4_five_records_keep_summaries_and_omit_payloads) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.216s

OK
```

Criterion 5 server output:

```text
command: python serve.py
health: HTTP 200 {"status":"ok"} in 1.67s
server stdout:

FitFindr is listening on http://localhost:5031
It runs one request at a time — a second one waits for the first.
Ask it something (single quotes, as always):

  curl -X POST http://localhost:5031/ask \
    -H 'Content-Type: application/json' \
    -d '{"query": "vintage graphic tee under $30"}'

Ctrl-C to stop.

 * Serving Flask app 'serve'
 * Debug mode: off
server stderr:
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5031
 * Running on http://192.168.1.9:5031
Press CTRL+C to quit
127.0.0.1 - - [11/Nov/2026 22:33:54] "GET /health HTTP/1.1" 200 -
```

## Run 2

Automated criteria 1–4:

```text
test_criterion_1_five_successful_runs_have_required_fields (test_serve.ServeCriteriaTests.test_criterion_1_five_successful_runs_have_required_fields) ... ok
test_criterion_2_three_failure_types_each_leave_error_record (test_serve.ServeCriteriaTests.test_criterion_2_three_failure_types_each_leave_error_record) ... ok
test_criterion_3_five_distinct_requests_append_in_order (test_serve.ServeCriteriaTests.test_criterion_3_five_distinct_requests_append_in_order) ... ok
test_criterion_4_five_records_keep_summaries_and_omit_payloads (test_serve.ServeCriteriaTests.test_criterion_4_five_records_keep_summaries_and_omit_payloads) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.212s

OK
```

Criterion 5 server output:

```text
command: python serve.py
health: HTTP 200 {"status":"ok"} in 1.52s
server stdout:

FitFindr is listening on http://localhost:5032
It runs one request at a time — a second one waits for the first.
Ask it something (single quotes, as always):

  curl -X POST http://localhost:5032/ask \
    -H 'Content-Type: application/json' \
    -d '{"query": "vintage graphic tee under $30"}'

Ctrl-C to stop.

 * Serving Flask app 'serve'
 * Debug mode: off
server stderr:
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5032
 * Running on http://192.168.1.9:5032
Press CTRL+C to quit
127.0.0.1 - - [11/Nov/2026 22:33:58] "GET /health HTTP/1.1" 200 -
```

## Run 3

Automated criteria 1–4:

```text
test_criterion_1_five_successful_runs_have_required_fields (test_serve.ServeCriteriaTests.test_criterion_1_five_successful_runs_have_required_fields) ... ok
test_criterion_2_three_failure_types_each_leave_error_record (test_serve.ServeCriteriaTests.test_criterion_2_three_failure_types_each_leave_error_record) ... ok
test_criterion_3_five_distinct_requests_append_in_order (test_serve.ServeCriteriaTests.test_criterion_3_five_distinct_requests_append_in_order) ... ok
test_criterion_4_five_records_keep_summaries_and_omit_payloads (test_serve.ServeCriteriaTests.test_criterion_4_five_records_keep_summaries_and_omit_payloads) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.225s

OK
```

Criterion 5 server output:

```text
command: python serve.py
health: HTTP 200 {"status":"ok"} in 1.53s
server stdout:

FitFindr is listening on http://localhost:5033
It runs one request at a time — a second one waits for the first.
Ask it something (single quotes, as always):

  curl -X POST http://localhost:5033/ask \
    -H 'Content-Type: application/json' \
    -d '{"query": "vintage graphic tee under $30"}'

Ctrl-C to stop.

 * Serving Flask app 'serve'
 * Debug mode: off
server stderr:
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5033
 * Running on http://192.168.1.9:5033
Press CTRL+C to quit
127.0.0.1 - - [11/Nov/2026 22:34:02] "GET /health HTTP/1.1" 200 -
```
