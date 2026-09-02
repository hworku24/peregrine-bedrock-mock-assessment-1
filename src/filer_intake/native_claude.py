"""Stretch task: use Anthropic's provider-native InvokeModel request format."""

from __future__ import annotations

import json
from typing import Any

from .errors import ModelResponseError


def invoke_claude_native(
    client: Any,
    model_id: str,
    prompt: str,
    *,
    max_tokens: int = 128,
) -> str:
    """Invoke Claude through Bedrock and return its first non-blank text block."""

    # TODO: implement the stretch task.
    # Required request fields:
    #   anthropic_version="bedrock-2023-05-31"
    #   max_tokens=max_tokens
    #   messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    # Call client.invoke_model with JSON contentType and accept values.
    # Read response["body"], parse its JSON, and validate its content blocks.
    raise NotImplementedError
