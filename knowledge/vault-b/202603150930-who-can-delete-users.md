# 202603150930 Who can delete a user

- ADMIN+ of the same tenant ([[202601051030-tenant-roles]],
  [[202602151100-tenant-isolation-404]]).
- An ADMIN does not delete an OWNER → 403 `OWNER_PROTECTED`
  ([[202602101415-owner-protection]]).
- **Nobody deletes themselves** → 422 `CANNOT_DELETE_SELF`. Two reasons:
  prevents accidental orphan tenants and limits stolen-session damage.
- Deletion itself is always soft ([[202603150900-soft-delete-30-days]]) and
  audits `USER_SOFT_DELETED` with targetId = the deleted user
  ([[202601201300-mutation-audit-log]]).
