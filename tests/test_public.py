import json
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from filer_intake import (
    BedrockInvocationError,
    ModelResponseError,
    SubmissionValidationError,
    build_messages,
    invoke_analysis,
    parse_analysis,
    process_submission,
    route_submission,
    validate_submission,
)


@pytest.fixture
def submission():
    return {
        "submission_id": "F-1001",
        "ocr_text": "Initial filing for Northwind Trade Council. Registration 104882.",
        "ocr_confidence": 0.97,
    }


def converse_response(payload):
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": json.dumps(payload)}],
            }
        },
        "stopReason": "end_turn",
        "usage": {"inputTokens": 40, "outputTokens": 25, "totalTokens": 65},
    }


def valid_analysis(**overrides):
    analysis = {
        "document_type": "initial",
        "registration_id": "104882",
        "applicant_name": "Northwind Trade Council",
        "flags": [],
        "confidence": 0.96,
    }
    analysis.update(overrides)
    return analysis


@pytest.mark.parametrize(
    "bad_submission",
    [
        None,
        {},
        {"submission_id": " ", "ocr_text": "text", "ocr_confidence": 0.9},
        {"submission_id": "F-1", "ocr_text": " ", "ocr_confidence": 0.9},
        {"submission_id": "F-1", "ocr_text": "text", "ocr_confidence": True},
        {"submission_id": "F-1", "ocr_text": "text", "ocr_confidence": 1.1},
    ],
)
def test_validate_submission_rejects_invalid_input(bad_submission):
    with pytest.raises(SubmissionValidationError):
        validate_submission(bad_submission)


def test_build_messages_marks_ocr_as_untrusted_and_serializes_input(submission):
    messages = build_messages(submission)

    assert messages[0]["role"] == "user"
    prompt = messages[0]["content"][0]["text"]
    assert "untrusted" in prompt.lower()
    assert "return only" in prompt.lower()
    assert "F-1001" in prompt
    assert "Northwind Trade Council" in prompt


def test_invoke_analysis_calls_converse_and_parses_json(submission):
    client = Mock(spec=["converse"])
    client.converse.return_value = converse_response(valid_analysis())

    result = invoke_analysis(client, "test-model", submission)

    assert result == valid_analysis()
    client.converse.assert_called_once_with(
        modelId="test-model",
        messages=build_messages(submission),
        inferenceConfig={"maxTokens": 250, "temperature": 0},
    )


def test_parse_analysis_rejects_invalid_json():
    response = {"output": {"message": {"content": [{"text": "not-json"}]}}}

    with pytest.raises(ModelResponseError):
        parse_analysis(response)


def test_invoke_analysis_preserves_aws_error_context(submission):
    client = Mock(spec=["converse"])
    client.converse.side_effect = ClientError(
        {
            "Error": {"Code": "ThrottlingException", "Message": "Too many requests"},
            "ResponseMetadata": {
                "HTTPStatusCode": 429,
                "RequestId": "request-123",
                "RetryAttempts": 2,
            },
        },
        "Converse",
    )

    with pytest.raises(BedrockInvocationError) as captured:
        invoke_analysis(client, "test-model", submission)

    error = captured.value
    assert error.error_code == "ThrottlingException"
    assert error.status_code == 429
    assert error.request_id == "request-123"
    assert error.retry_attempts == 2
    assert error.retryable is True
    assert error.__cause__ is client.converse.side_effect


@pytest.mark.parametrize(
    ("analysis", "expected_reason"),
    [
        (valid_analysis(confidence=0.50), "low_model_confidence"),
        (valid_analysis(registration_id=None), "missing_registration_id"),
        (valid_analysis(applicant_name=None), "missing_applicant_name"),
        (valid_analysis(flags=["missing_signature"]), "flag:missing_signature"),
    ],
)
def test_route_submission_sends_uncertainty_to_review(
    submission, analysis, expected_reason
):
    route, reasons = route_submission(submission, analysis)

    assert route == "HUMAN_REVIEW"
    assert expected_reason in reasons


def test_process_submission_skips_bedrock_for_low_ocr_confidence(submission):
    client = Mock(spec=["converse"])
    low_quality = {**submission, "ocr_confidence": 0.40}

    result = process_submission(client, "test-model", low_quality)

    assert result == {
        "submission_id": "F-1001",
        "route": "HUMAN_REVIEW",
        "reasons": ["low_ocr_confidence"],
        "analysis": None,
        "audit": {"model_id": "test-model", "bedrock_called": False},
    }
    client.converse.assert_not_called()
