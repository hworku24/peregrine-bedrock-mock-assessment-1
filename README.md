# Federal Filer Intake — Mock Technical Assessment 1

## Candidate instructions

You have **90 minutes**. Work in Python and use the supplied Bedrock-compatible client.
You may use official documentation and ordinary web search. For a realistic rehearsal,
close AI assistants before starting, share the full practice screen, and narrate your
reasoning as you work.

There are several tasks. You might not finish all of them. Prioritize a small, correct,
tested path over unfinished breadth. Do not make real AWS calls during the timed attempt.

## Scenario

A federal agency receives filer applications as scanned documents. An OCR service has
already produced text and a confidence score. Your service must:

1. validate each submission;
2. ask an Amazon Bedrock model to extract a small structured record;
3. validate the model response instead of trusting it;
4. apply deterministic routing rules; and
5. retain enough context to audit the decision.

The model may help extract information and may route uncertainty to a person. It must
never independently reject an application.

## Start here

```bash
python -m pytest -q
git status
```

Read these files before editing:

- `src/filer_intake/service.py`
- `src/filer_intake/errors.py`
- `tests/test_public.py`

Keep the public function names and arguments unchanged. You may add private helpers.

## Expected model output

Bedrock should return JSON text matching this shape:

```json
{
  "document_type": "initial",
  "registration_id": "104882",
  "applicant_name": "Northwind Trade Council",
  "flags": [],
  "confidence": 0.96
}
```

Allowed document types:

- `initial`
- `amendment`
- `renewal`

Allowed flags:

- `missing_signature`
- `identity_mismatch`
- `ambiguous_registration_id`
- `late_filing`
- `poor_scan`

## Task 1 — Validate input and build messages

Implement `validate_submission()` and `build_messages()`.

A valid submission is a mapping containing:

- `submission_id`: non-blank string;
- `ocr_text`: non-blank string; and
- `ocr_confidence`: an `int` or `float` from `0.0` through `1.0`. A Boolean is invalid,
  even though `bool` is a subclass of `int` in Python.

The message must tell the model to return only the required JSON object. Clearly mark OCR
text as untrusted data, not instructions. Serialize the input record with `json.dumps()`
so quotes, newlines, and non-ASCII names are preserved safely.

## Task 2 — Call and validate Bedrock

Implement `invoke_analysis()` and `parse_analysis()`.

Call `client.converse()` exactly once with:

```python
modelId=model_id
messages=build_messages(submission)
inferenceConfig={"maxTokens": 250, "temperature": 0}
```

Requirements:

- Catch `botocore.exceptions.ClientError`.
- Preserve `Error.Code`, `Error.Message`, `HTTPStatusCode`, `RequestId`, and
  `RetryAttempts` when raising `BedrockInvocationError`.
- Preserve the original exception with `raise ... from exc`.
- A status of `408`, `429`, or `>= 500` is retryable. Other status values are not.
- Locate the first non-blank text block in the Converse response.
- Parse it with `json.loads()` and validate every required field.
- Reject malformed JSON, missing or extra keys, unknown enum values, duplicate flags,
  blank identifiers/names, Boolean confidence values, and confidence outside `[0, 1]` by
  raising `ModelResponseError`.
- Do not silently manufacture missing model data.

## Task 3 — Apply deterministic routing

Implement `route_submission()`.

Return `(route, reasons)` where route is `AUTO_CLEAR` or `HUMAN_REVIEW`.

Route to `HUMAN_REVIEW` when any of these is true:

- OCR confidence is below `0.80`;
- model confidence is below `0.90`;
- registration ID or applicant name is missing; or
- a critical flag is present: `missing_signature`, `identity_mismatch`, or
  `ambiguous_registration_id`.

Reason strings must be deterministic:

- `low_ocr_confidence`
- `low_model_confidence`
- `missing_registration_id`
- `missing_applicant_name`
- `flag:<flag-name>` for each critical flag, ordered alphabetically

If none apply, return `("AUTO_CLEAR", [])`. `late_filing` and `poor_scan` remain audit
signals but do not independently force review under this exercise's supplied rules.

## Task 4 — Orchestrate one submission

Implement `process_submission()`.

- Validate first.
- If OCR confidence is below `0.80`, return a `HUMAN_REVIEW` result without calling
  Bedrock. Set `analysis` to `None` and `audit.bedrock_called` to `False`.
- Otherwise call Bedrock, route the analysis, and set `audit.bedrock_called` to `True`.
- Include `submission_id`, `route`, `reasons`, `analysis`, and an `audit` dictionary with
  `model_id` and `bedrock_called`.
- Do not mutate the input mapping.
- Let `BedrockInvocationError` and `ModelResponseError` propagate. An upstream workflow
  needs to distinguish retryable outages from model-contract failures.

## Task 5 — Tests

Add at least three focused tests of your own. Include one failure path. Keep tests free of
network calls and credentials.

## Stretch task — Provider-native Claude request

If time remains, implement `invoke_claude_native()` in `native_claude.py` using
`client.invoke_model()`, `json.dumps()`, `response["body"].read()`, and `json.loads()`.

## What the panel is observing

- How you turn prose into a checklist
- Python correctness and clarity
- Understanding of dictionaries, JSON, exceptions, and mocks
- Judgment at the boundary between probabilistic model output and deterministic rules
- Whether errors and decisions remain diagnosable
- How you use test results and communicate tradeoffs

## Optional live AWS test

Only after completing the timed mock, follow `docs/aws-live-setup.md`. The default test
suite never calls AWS.
