# 202601201300 Mutation audit log

Every EFFECTIVE mutation of a user/invitation/role writes an AuditEntry to the
auditLog, in the same operation (no "I'll audit later"). Denied attempts
(403/422) do NOT produce an entry.

Fields: `id` (new UUID), `tenantId`, `actorId` (the `X-Actor-Id`), `action`,
`targetId` (id of the affected resource), `timestamp` (UTC Instant), `details`
(free, optional).

Valid actions — do not invent strings outside this list, compliance dashboards
break:

- `USER_INVITED` (targetId = invitation id)
- `INVITATION_RESENT` (targetId = invitation id)
- `USER_ROLE_CHANGED` (targetId = user id)
- `USER_SOFT_DELETED` (targetId = user id)
- `USER_RESTORED` (targetId = user id)

Links to everything: [[202602041100-invitation-72h-expiry]],
[[202603150900-soft-delete-30-days]], [[202601051030-tenant-roles]].
