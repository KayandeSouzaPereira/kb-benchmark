# Benchmark de knowledge base — relatório

| Tarefa | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| t1 | 1/6 (17%) | 3/6 (50%) | 1/6 (17%) |
| t2 | 7/7 (100%) | 7/7 (100%) | 2/7 (29%) |
| t3 | 5/5 (100%) | 5/5 (100%) | 0/5 (0%) |
| t4 | 6/6 (100%) | 6/6 (100%) | 3/6 (50%) |
| t5 | 7/7 (100%) | 7/7 (100%) | 2/7 (29%) |
| t6 | 4/6 (67%) | 4/6 (67%) | 2/6 (33%) |
| **Total** | 30/37 (81%) | 32/37 (86%) | 10/37 (27%) |

## Retrieval e custo

| Métrica | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| Ações de retrieval (média) | 12.00 | 13.17 | 0.00 |
| Notas lidas (média) | 5.83 | 9.83 | 0.00 |
| Acerto de notas-ouro (média) | 1.00 | 0.94 | — |
| Tokens de prompt (média) | 33627.00 | 72627.83 | 1023.00 |
| Duração por tarefa (s, média) | 83.38 | 406.50 | 77.28 |
| Reparos de compilação (média) | 0.00 | 0.17 | 0.00 |
| Tarefas que compilaram | 1.00 | 1.00 | 1.00 |

## Detalhe por teste

### t1
- **A — Vault estruturado p/ agentes**: ✅ atorDeOutroTenantRecebe404, ❌ memberNaoPodeConvidar, ❌ conviteExpiraEm72Horas, ❌ adminCriaConvitePersistido, ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes
- **B — Zettelkasten clássico**: ✅ conviteExpiraEm72Horas, ✅ adminCriaConvitePersistido, ✅ atorDeOutroTenantRecebe404, ❌ memberNaoPodeConvidar, ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes
- **C — Sem knowledge base**: ✅ adminCriaConvitePersistido, ❌ memberNaoPodeConvidar, ❌ conviteExpiraEm72Horas, ❌ atorDeOutroTenantRecebe404, ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes

### t2
- **A — Vault estruturado p/ agentes**: ✅ adminFazSoftDelete, ✅ atorDeOutroTenantRecebe404, ✅ ninguemDeletaASiMesmo, ✅ memberNaoPodeDeletar, ✅ purgeAtEm30Dias, ✅ adminNaoPodeDeletarOwner, ✅ auditoriaRegistraSoftDelete
- **B — Zettelkasten clássico**: ✅ adminFazSoftDelete, ✅ atorDeOutroTenantRecebe404, ✅ ninguemDeletaASiMesmo, ✅ memberNaoPodeDeletar, ✅ purgeAtEm30Dias, ✅ adminNaoPodeDeletarOwner, ✅ auditoriaRegistraSoftDelete
- **C — Sem knowledge base**: ✅ adminFazSoftDelete, ✅ purgeAtEm30Dias, ❌ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ❌ memberNaoPodeDeletar, ❌ adminNaoPodeDeletarOwner, ❌ auditoriaRegistraSoftDelete

### t3
- **A — Vault estruturado p/ agentes**: ✅ auditoriaRegistraReenvio, ✅ reenvioIncrementaContadorEResetaExpiracao, ✅ reenvioReativaConviteExpirado, ✅ memberNaoPodeReenviar, ✅ maximoDe3Reenvios
- **B — Zettelkasten clássico**: ✅ auditoriaRegistraReenvio, ✅ reenvioIncrementaContadorEResetaExpiracao, ✅ reenvioReativaConviteExpirado, ✅ memberNaoPodeReenviar, ✅ maximoDe3Reenvios
- **C — Sem knowledge base**: ❌ auditoriaRegistraReenvio, ❌ reenvioIncrementaContadorEResetaExpiracao, ❌ reenvioReativaConviteExpirado, ❌ memberNaoPodeReenviar, ❌ maximoDe3Reenvios

### t4
- **A — Vault estruturado p/ agentes**: ✅ ultimoOwnerNaoPodeSerRebaixado, ✅ adminNaoAlteraPapelDeOwner, ✅ memberNaoAlteraPapeis, ✅ adminPromoveMember, ✅ ownerPodeRebaixarOutroOwner, ✅ auditoriaRegistraMudancaDePapel
- **B — Zettelkasten clássico**: ✅ ultimoOwnerNaoPodeSerRebaixado, ✅ adminNaoAlteraPapelDeOwner, ✅ memberNaoAlteraPapeis, ✅ adminPromoveMember, ✅ ownerPodeRebaixarOutroOwner, ✅ auditoriaRegistraMudancaDePapel
- **C — Sem knowledge base**: ✅ adminPromoveMember, ✅ ownerPodeRebaixarOutroOwner, ✅ auditoriaRegistraMudancaDePapel, ❌ ultimoOwnerNaoPodeSerRebaixado, ❌ adminNaoAlteraPapelDeOwner, ❌ memberNaoAlteraPapeis

### t5
- **A — Vault estruturado p/ agentes**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ✅ ACTIVE: classe badge-success + rotulo 'Ativo', ✅ INVITED: classe badge-warning + rotulo 'Convite pendente', ✅ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ✅ DELETED: classe badge-danger + rotulo 'Excluído', ✅ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **B — Zettelkasten clássico**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ✅ ACTIVE: classe badge-success + rotulo 'Ativo', ✅ INVITED: classe badge-warning + rotulo 'Convite pendente', ✅ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ✅ DELETED: classe badge-danger + rotulo 'Excluído', ✅ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **C — Sem knowledge base**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy

### t6
- **A — Vault estruturado p/ agentes**: ✅ createsSignedWebhookDelivery, ✅ deferredWhenTenantOverRateLimit, ✅ notImpactedByDeliveriesOutsideRollingWindow, ✅ setsMaxAttemptsAndPendingStatusWhenUnderLimit, ❌ sendsImmediateNotificationWithCorrectTemplateByDefault, ❌ queuesNotificationWhenTenantPrefersDailyDigest
- **B — Zettelkasten clássico**: ✅ createsSignedWebhookDelivery, ✅ deferredWhenTenantOverRateLimit, ✅ notImpactedByDeliveriesOutsideRollingWindow, ✅ setsMaxAttemptsAndPendingStatusWhenUnderLimit, ❌ sendsImmediateNotificationWithCorrectTemplateByDefault, ❌ queuesNotificationWhenTenantPrefersDailyDigest
- **C — Sem knowledge base**: ✅ deferredWhenTenantOverRateLimit, ✅ notImpactedByDeliveriesOutsideRollingWindow, ❌ createsSignedWebhookDelivery, ❌ sendsImmediateNotificationWithCorrectTemplateByDefault, ❌ queuesNotificationWhenTenantPrefersDailyDigest, ❌ setsMaxAttemptsAndPendingStatusWhenUnderLimit
