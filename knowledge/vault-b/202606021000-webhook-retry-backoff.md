# 202606021000 Webhook retry / backoff policy

New `WebhookDelivery` always gets **`maxAttempts = 5`**, `attemptCount = 0`.
Status starts `PENDING` — unless the tenant is over the rate limit, then
`DEFERRED` ([[202606040930-outbound-webhook-rate-limit]]).

Backoff schedule for retries: 1min, 5min, 30min, 2h, 12h. After maxAttempts
failures → status `FAILED`, endpoint gets flagged
([[202606021300-endpoint-disabling-on-failures]]).

Related: [[202606020930-webhook-signing]].
