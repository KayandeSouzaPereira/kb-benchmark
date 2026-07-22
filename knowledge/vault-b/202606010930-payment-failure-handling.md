# 202606010930 Payment failure handling

When a subscription payment fails, three things need to happen and none of
the rules live here — this note is just the map of what to touch:

1. Record + send a webhook, event type `payment.failed`. Signing:
   [[202606020930-webhook-signing]]. Retry/backoff:
   [[202606021000-webhook-retry-backoff]].
2. Notify the billing contact. Template:
   [[202606030930-email-template-mapping]]. Digest mode decides SENT vs
   QUEUED: [[202606031000-digest-mode-preferences]].
3. Check the tenant's outbound webhook rate limit BEFORE creating the
   delivery: [[202606040930-outbound-webhook-rate-limit]].

Dunning schedule (day 1/3/7 emails, suspend day 10) is a separate scheduled
job, not part of this event handler — not detailing it here.

Related: [[202606011000-proration-rules]], [[202606011130-subscription-cancellation]].
