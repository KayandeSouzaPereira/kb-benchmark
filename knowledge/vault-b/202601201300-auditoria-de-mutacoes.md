# 202601201300 Auditoria de mutações

Toda mutação EFETIVADA de usuário/convite/papel grava um AuditEntry no
auditLog, na mesma operação (nada de "audito depois"). Tentativa negada
(403/422) NÃO gera entrada.

Campos: `id` (UUID novo), `tenantId`, `actorId` (o `X-Actor-Id`), `action`,
`targetId` (id do recurso afetado), `timestamp` (Instant UTC), `details`
(livre, opcional).

Ações válidas — não inventar strings fora desta lista, dashboards de
compliance quebram:

- `USER_INVITED` (targetId = id do convite)
- `INVITATION_RESENT` (targetId = id do convite)
- `USER_ROLE_CHANGED` (targetId = id do usuário)
- `USER_SOFT_DELETED` (targetId = id do usuário)
- `USER_RESTORED` (targetId = id do usuário)

Liga com tudo: [[202602041100-expiracao-de-convites-72h]],
[[202603150900-soft-delete-30-dias]], [[202601051030-papeis-do-tenant]].
