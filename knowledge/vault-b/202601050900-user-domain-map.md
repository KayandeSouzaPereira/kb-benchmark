# 202601050900 Map — user management domain

Index note for everything I've thought through about the product's user domain.

- Roles and hierarchy: [[202601051030-tenant-roles]]
- Special owner protections: [[202602101415-owner-protection]] and [[202602101430-last-owner]]
- Tenant isolation: [[202602151100-tenant-isolation-404]]
- Seat limits: [[202601121000-plan-seat-limits]] (mind the correction in [[202605021430-pending-invitations-count]])
- Invitations: [[202602041100-invitation-72h-expiry]], [[202602041130-invitation-resend]]
- Deletion: [[202603150900-soft-delete-30-days]], [[202603150930-who-can-delete-users]]
- Auditing: [[202601201300-mutation-audit-log]]
- Authentication (separate from user management): [[202601080800-lockout-and-passwords]]

Code conventions live in another map: [[202604010900-api-and-conventions-map]].

Newer areas that grew big enough for their own maps (not really part of
"user management" anymore, but worth linking from here since payment
failures do touch user-adjacent stuff like notifications):
[[202606010900-billing-map]], [[202606020900-webhooks-map]],
[[202606030900-notifications-map]], [[202606040900-rate-limiting-map]],
[[202606050900-sso-map]].
