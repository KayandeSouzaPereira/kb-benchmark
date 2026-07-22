# 202606040930 Outbound webhook rate limit

Max **10 webhook deliveries created per tenant in a rolling 60-minute
window**. When creating a new `WebhookDelivery` (any event type), count
existing deliveries for that tenant with `createdAt` in the last 60 min —
if already **≥ 10**, the new delivery gets status **`DEFERRED`** instead of
`PENDING`. Not rejected, not dropped — just deferred behind the limit.

Check happens BEFORE signing, applies to every event type equally. See
[[202606020930-webhook-signing]] and
[[202606010930-payment-failure-handling]].

Related: [[202606041030-per-plan-rate-tiers]] (that one is for the public
API, this one is flat 10/hour regardless of plan — don't mix them up).
