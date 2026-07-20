# 202601080800 Lockout and password policy

Password: minimum 12 characters, 1 digit, 1 symbol; last 5 not reusable.

Lockout: 5 consecutive login failures → 15-minute lock. Counter resets on
successful login or lock expiry. ADMIN+ may unlock manually (audited —
[[202601201300-mutation-audit-log]]).

Note: this is authentication, not user management; kept separate from the map
[[202601050900-user-domain-map]].
