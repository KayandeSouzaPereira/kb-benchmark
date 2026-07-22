# 202606031330 ADR — payment_failed retired for payment_failed_v2

`payment_failed` (v1) had a broken invoice-link merge tag. Retired
2026-05-25. Every code path must use `payment_failed_v2` now — don't bring
the old id back.

Related: [[202606030930-email-template-mapping]].
