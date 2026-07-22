---
type: business-rule
system: billing
status: active
updated: 2026-06-10
---

# Payment failure handling

When a subscription payment fails, the billing worker calls the internal
event pipeline, which must:

1. **Record and send a webhook delivery** with event type `payment.failed`
   to the tenant's registered webhook endpoint. Signing and retry rules are
   NOT defined here — see
   [../webhooks/webhook-signing.md](../webhooks/webhook-signing.md) and
   [../webhooks/retry-backoff-policy.md](../webhooks/retry-backoff-policy.md).
2. **Notify the tenant's billing contact.** Template and delivery timing are
   NOT defined here — see
   [../notifications/email-template-mapping.md](../notifications/email-template-mapping.md)
   and
   [../notifications/digest-mode-preferences.md](../notifications/digest-mode-preferences.md).
3. **Respect the tenant's outbound webhook rate limit** before creating the
   delivery — see
   [../rate-limiting/outbound-webhook-rate-limit.md](../rate-limiting/outbound-webhook-rate-limit.md).

## Dunning schedule (informational — not required for the webhook/notify flow)

Failed payments trigger a dunning e-mail sequence at day 1, day 3 and day 7.
On day 10 the subscription is suspended. This schedule is handled by a
separate scheduled job, not by the payment-failure event handler.

## Related

- [proration-rules.md](proration-rules.md)
- [subscription-cancellation.md](subscription-cancellation.md)
