# 202606021300 Disabling endpoints after repeated failures

3 consecutive `FAILED` deliveries (retries exhausted) → endpoint
auto-disabled, in-app notification to admins. Re-enable requires explicit
admin action.

Related: [[202606021000-webhook-retry-backoff]].
