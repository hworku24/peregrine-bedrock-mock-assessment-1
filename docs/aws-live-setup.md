# Optional live AWS smoke test

Do this only after the timed assessment. The unit tests use mocks and make no AWS calls.

## Safety rules

- Never create access keys for the AWS root user.
- Never commit credentials, `.env`, or an `.aws` directory.
- Prefer short-lived credentials through IAM Identity Center or another approved role.
- Keep `maxTokens` small and delete credentials from the Codespace when finished.
- Use a model or inference profile currently available in your chosen AWS Region.

## Authenticate

The AWS CLI and Boto3 use the standard AWS credential provider chain. In a Codespace,
authenticate with your organization's approved short-lived method. For IAM Identity
Center, the usual flow is:

```bash
aws configure sso
aws sso login
aws sts get-caller-identity
```

Do not paste credentials into Python source or interview chat.

## Select configuration

```bash
export AWS_REGION="us-east-1"
export BEDROCK_MODEL_ID="the-model-or-inference-profile-id-you-can-access"
export RUN_LIVE_BEDROCK="1"
```

## Run exactly one small request

```bash
python scripts/live_bedrock_smoke.py
```

The script refuses to run unless `RUN_LIVE_BEDROCK=1` and `BEDROCK_MODEL_ID` are set.
Running it may incur a small AWS charge.
