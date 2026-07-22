# 202606041300 Internal service exemption

Internal service-to-service calls (mTLS cert, not API key) are exempt from
public API limits. Outbound webhook limit still applies to internal billing
events though — it protects the tenant's endpoint, not our API.
