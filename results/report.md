# Benchmark de knowledge base — relatório

| Tarefa | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| t1 | 4/6 (67%) | 4/6 (67%) | 1/6 (17%) |
| t2 | 4/7 (57%) | 3/7 (43%) | 2/7 (29%) |
| t3 | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) |
| t4 | 6/6 (100%) | 6/6 (100%) | 3/6 (50%) |
| t5 | 2/7 (29%) | 2/7 (29%) | 2/7 (29%) |
| **Total** | 21/31 (68%) | 15/31 (48%) | 8/31 (26%) |

## Retrieval e custo

| Métrica | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| Ações de retrieval (média) | 6.20 | 6.60 | 0.00 |
| Notas lidas (média) | 3.40 | 4.80 | 0.00 |
| Acerto de notas-ouro (média) | 0.67 | 0.67 | — |
| Tokens de prompt (média) | 12612.80 | 14411.60 | 690.20 |
| Duração por tarefa (s, média) | 79.84 | 116.38 | 70.06 |
| Reparos de compilação (média) | 0.00 | 0.20 | 0.00 |
| Tarefas que compilaram | 1.00 | 1.00 | 1.00 |

## Detalhe por teste

### t1
- **A — Vault estruturado p/ agentes**: ✅ conviteExpiraEm72Horas, ✅ adminCriaConvitePersistido, ✅ atorDeOutroTenantRecebe404, ✅ auditoriaRegistraUserInvited, ❌ memberNaoPodeConvidar, ❌ limiteDoPlanoFreeContaConvitesPendentes
- **B — Zettelkasten clássico**: ✅ memberNaoPodeConvidar, ✅ conviteExpiraEm72Horas, ✅ adminCriaConvitePersistido, ✅ auditoriaRegistraUserInvited, ❌ atorDeOutroTenantRecebe404, ❌ limiteDoPlanoFreeContaConvitesPendentes
- **C — Sem knowledge base**: ✅ adminCriaConvitePersistido, ❌ memberNaoPodeConvidar, ❌ conviteExpiraEm72Horas, ❌ atorDeOutroTenantRecebe404, ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes

### t2
- **A — Vault estruturado p/ agentes**: ✅ adminFazSoftDelete, ✅ atorDeOutroTenantRecebe404, ✅ purgeAtEm30Dias, ✅ auditoriaRegistraSoftDelete, ❌ ninguemDeletaASiMesmo, ❌ memberNaoPodeDeletar, ❌ adminNaoPodeDeletarOwner
- **B — Zettelkasten clássico**: ✅ adminFazSoftDelete, ✅ purgeAtEm30Dias, ✅ auditoriaRegistraSoftDelete, ❌ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ❌ memberNaoPodeDeletar, ❌ adminNaoPodeDeletarOwner
- **C — Sem knowledge base**: ✅ adminFazSoftDelete, ✅ purgeAtEm30Dias, ❌ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ❌ memberNaoPodeDeletar, ❌ adminNaoPodeDeletarOwner, ❌ auditoriaRegistraSoftDelete

### t3
- **A — Vault estruturado p/ agentes**: ✅ auditoriaRegistraReenvio, ✅ reenvioIncrementaContadorEResetaExpiracao, ✅ reenvioReativaConviteExpirado, ✅ memberNaoPodeReenviar, ✅ maximoDe3Reenvios
- **B — Zettelkasten clássico**: ❌ auditoriaRegistraReenvio, ❌ reenvioIncrementaContadorEResetaExpiracao, ❌ reenvioReativaConviteExpirado, ❌ memberNaoPodeReenviar, ❌ maximoDe3Reenvios
- **C — Sem knowledge base**: ❌ auditoriaRegistraReenvio, ❌ reenvioIncrementaContadorEResetaExpiracao, ❌ reenvioReativaConviteExpirado, ❌ memberNaoPodeReenviar, ❌ maximoDe3Reenvios

### t4
- **A — Vault estruturado p/ agentes**: ✅ ultimoOwnerNaoPodeSerRebaixado, ✅ adminNaoAlteraPapelDeOwner, ✅ memberNaoAlteraPapeis, ✅ adminPromoveMember, ✅ ownerPodeRebaixarOutroOwner, ✅ auditoriaRegistraMudancaDePapel
- **B — Zettelkasten clássico**: ✅ ultimoOwnerNaoPodeSerRebaixado, ✅ adminNaoAlteraPapelDeOwner, ✅ memberNaoAlteraPapeis, ✅ adminPromoveMember, ✅ ownerPodeRebaixarOutroOwner, ✅ auditoriaRegistraMudancaDePapel
- **C — Sem knowledge base**: ✅ adminPromoveMember, ✅ ownerPodeRebaixarOutroOwner, ✅ auditoriaRegistraMudancaDePapel, ❌ ultimoOwnerNaoPodeSerRebaixado, ❌ adminNaoAlteraPapelDeOwner, ❌ memberNaoAlteraPapeis

### t5
- **A — Vault estruturado p/ agentes**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **B — Zettelkasten clássico**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **C — Sem knowledge base**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
