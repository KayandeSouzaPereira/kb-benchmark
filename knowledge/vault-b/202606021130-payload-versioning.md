# 202606021130 Webhook payload versioning

Every payload has `"apiVersion": "2026-01-01"`. Breaking changes ship as a
new dated version, opt-in via dashboard. Additive fields don't bump it.
