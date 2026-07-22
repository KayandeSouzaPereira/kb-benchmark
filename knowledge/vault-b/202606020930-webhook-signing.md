# 202606020930 Webhook signing

Every delivery is signed with **HMAC-SHA256** over the raw JSON body, using
the tenant's webhook secret. Store the signature as a lowercase hex string
(64 chars) on the `WebhookDelivery` — no `sha256=` prefix, no colons, just
the raw hex digest.

Sign every delivery including retries (recompute, don't reuse). Never sign
with the API key — that's a different credential from the webhook secret.

Related: [[202606021000-webhook-retry-backoff]],
[[202606010930-payment-failure-handling]].
