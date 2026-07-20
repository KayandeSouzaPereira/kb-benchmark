# 202601201330 API error codes

Standard business-error envelope (`code` is a stable contract, `message` is
free):

```json
{ "code": "STABLE_CODE", "message": "human text" }
```

Codes we've settled on:

- 403 `FORBIDDEN_ROLE` — insufficient role ([[202601051030-tenant-roles]])
- 403 `OWNER_PROTECTED` — admin touching an owner ([[202602101415-owner-protection]])
- 409 `LAST_OWNER` — tenant would be left ownerless ([[202602101430-last-owner]])
- 422 `PLAN_LIMIT_EXCEEDED` — seat limit ([[202605021430-pending-invitations-count]])
- 422 `CANNOT_DELETE_SELF` — self-deletion ([[202603150930-who-can-delete-users]])
- 422 `RESEND_LIMIT_REACHED` — 4th resend ([[202602041130-invitation-resend]])
- 410 `INVITATION_EXPIRED` — accepting an expired invite ([[202602041100-invitation-72h-expiry]])
- 404 `NOT_FOUND` — nonexistent OR actor from another tenant ([[202602151100-tenant-isolation-404]])

No stacktraces in the body, ever.
