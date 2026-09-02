"""Read-only readiness check. This script never calls AWS."""

from __future__ import annotations

import platform
import shutil

import boto3


def main() -> None:
    print(f"Python: {platform.python_version()}")
    print(f"boto3: {boto3.__version__}")
    print(f"AWS CLI: {'available' if shutil.which('aws') else 'not found (optional for mocks)'}")
    print("Live AWS call: disabled")
    print("Ready: run python -m pytest -q")


if __name__ == "__main__":
    main()
