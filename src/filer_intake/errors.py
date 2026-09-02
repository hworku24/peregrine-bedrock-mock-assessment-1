"""Application-level exceptions for the assessment."""


class SubmissionValidationError(ValueError):
    """Raised when a caller supplies an invalid submission."""


class ModelResponseError(ValueError):
    """Raised when Bedrock returns output that violates the expected contract."""


class BedrockInvocationError(RuntimeError):
    """A diagnosable wrapper around an AWS service error."""

    def __init__(
        self,
        *,
        error_code: str,
        message: str,
        status_code: int | None,
        request_id: str | None,
        retry_attempts: int,
        retryable: bool,
    ) -> None:
        self.error_code = error_code
        self.status_code = status_code
        self.request_id = request_id
        self.retry_attempts = retry_attempts
        self.retryable = retryable
        super().__init__(
            "Bedrock request failed: "
            f"code={error_code}, status={status_code}, request_id={request_id}, "
            f"retry_attempts={retry_attempts}, message={message}"
        )
