# 202606041000 API key rotation

2 active keys per tenant allowed simultaneously (public REST API keys, not
webhook secrets) for zero-downtime rotation. Old key needs manual
revocation, no auto-expiry.
