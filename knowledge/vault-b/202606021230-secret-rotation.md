# 202606021230 Webhook secret rotation

Old secret stays valid for 24h after rotation (dual-signing window) so
in-flight retries still validate. After 24h, only the new secret works.
