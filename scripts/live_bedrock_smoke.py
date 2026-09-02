"""Opt-in, cost-bounded live Bedrock smoke test. Never imported by unit tests."""

from __future__ import annotations

import json
import os

import boto3
from botocore.config import Config

from filer_intake import process_submission


def main() -> None:
    if os.getenv("RUN_LIVE_BEDROCK") != "1":
        raise SystemExit("Refusing live call: set RUN_LIVE_BEDROCK=1 explicitly")

    model_id = os.getenv("BEDROCK_MODEL_ID")
    if not model_id:
        raise SystemExit("BEDROCK_MODEL_ID is required")

    region = os.getenv("AWS_REGION", "us-east-1")
    config = Config(
        connect_timeout=5,
        read_timeout=60,
        retries={"mode": "standard", "total_max_attempts": 3},
    )
    client = boto3.client("bedrock-runtime", region_name=region, config=config)

    result = process_submission(
        client,
        model_id,
        {
            "submission_id": "LIVE-SMOKE-1",
            "ocr_text": (
                "Initial application for Northwind Trade Council. "
                "Registration 104882. Signed August 25, 2026."
            ),
            "ocr_confidence": 0.98,
        },
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
