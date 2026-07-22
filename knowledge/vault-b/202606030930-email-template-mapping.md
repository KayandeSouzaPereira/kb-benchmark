# 202606030930 Email template mapping

Payment failure → **`templateId = "payment_failed_v2"`**. NOT
`payment_failed` (v1) — that one was retired, see
[[202606031330-template-retirement-adr]].

Other mappings while I'm at it: `user.invited` → `invite_v3`,
`subscription.cancelled` → `cancellation_confirmed_v1`.

Related: [[202606031000-digest-mode-preferences]],
[[202606010930-payment-failure-handling]].
