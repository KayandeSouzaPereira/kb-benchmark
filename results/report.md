# Benchmark de knowledge base — relatório

| Tarefa | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| t1 | 3/6 (50%) | 1/6 (17%) | 0/6 (0%) |
| t2 | 2/7 (29%) | 1/7 (14%) | 0/7 (0%) |
| t3 | 5/5 (100%) | 5/5 (100%) | 0/5 (0%) |
| t4 | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) |
| t5 | 2/7 (29%) | 6/7 (86%) | 2/7 (29%) |
| **Total** | 12/31 (39%) | 13/31 (42%) | 2/31 (6%) |

## Retrieval e custo

| Métrica | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| Ações de retrieval (média) | 6.40 | 6.80 | 0.00 |
| Notas lidas (média) | 1.80 | 5.20 | 0.00 |
| Acerto de notas-ouro (média) | 0.27 | 0.93 | — |
| Tokens de prompt (média) | 14032.60 | 18458.20 | 721.00 |
| Duração por tarefa (s, média) | 123.02 | 132.98 | 63.14 |
| Reparos de compilação (média) | 0.00 | 0.20 | 0.00 |
| Tarefas que compilaram | 1.00 | 1.00 | 1.00 |

## Detalhe por teste

### t1
- **A — Vault estruturado p/ agentes**: ✅ conviteExpiraEm72Horas, ✅ adminCriaConvitePersistido, ✅ auditoriaRegistraUserInvited, ❌ memberNaoPodeConvidar, ❌ atorDeOutroTenantRecebe404, ❌ limiteDoPlanoFreeContaConvitesPendentes
- **B — Zettelkasten clássico**: ✅ atorDeOutroTenantRecebe404, ❌ memberNaoPodeConvidar, ❌ conviteExpiraEm72Horas, ❌ adminCriaConvitePersistido, ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes
- **C — Sem knowledge base**: ❌ memberNaoPodeConvidar, ❌ conviteExpiraEm72Horas, ❌ adminCriaConvitePersistido, ❌ atorDeOutroTenantRecebe404, ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes

### t2
- **A — Vault estruturado p/ agentes**: ✅ adminFazSoftDelete, ✅ purgeAtEm30Dias, ❌ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ❌ memberNaoPodeDeletar, ❌ adminNaoPodeDeletarOwner, ❌ auditoriaRegistraSoftDelete
- **B — Zettelkasten clássico**: ✅ atorDeOutroTenantRecebe404, ❌ adminFazSoftDelete, ❌ ninguemDeletaASiMesmo, ❌ memberNaoPodeDeletar, ❌ purgeAtEm30Dias, ❌ adminNaoPodeDeletarOwner, ❌ auditoriaRegistraSoftDelete
- **C — Sem knowledge base**: ❌ adminFazSoftDelete, ❌ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ❌ memberNaoPodeDeletar, ❌ purgeAtEm30Dias, ❌ adminNaoPodeDeletarOwner, ❌ auditoriaRegistraSoftDelete

### t3
- **A — Vault estruturado p/ agentes**: ✅ auditoriaRegistraReenvio, ✅ reenvioIncrementaContadorEResetaExpiracao, ✅ reenvioReativaConviteExpirado, ✅ memberNaoPodeReenviar, ✅ maximoDe3Reenvios
- **B — Zettelkasten clássico**: ✅ auditoriaRegistraReenvio, ✅ reenvioIncrementaContadorEResetaExpiracao, ✅ reenvioReativaConviteExpirado, ✅ memberNaoPodeReenviar, ✅ maximoDe3Reenvios
- **C — Sem knowledge base**: ❌ auditoriaRegistraReenvio, ❌ reenvioIncrementaContadorEResetaExpiracao, ❌ reenvioReativaConviteExpirado, ❌ memberNaoPodeReenviar, ❌ maximoDe3Reenvios

### t4
- **A — Vault estruturado p/ agentes**: ❌ ultimoOwnerNaoPodeSerRebaixado, ❌ adminNaoAlteraPapelDeOwner, ❌ memberNaoAlteraPapeis, ❌ adminPromoveMember, ❌ ownerPodeRebaixarOutroOwner, ❌ auditoriaRegistraMudancaDePapel
- **B — Zettelkasten clássico**: ❌ ultimoOwnerNaoPodeSerRebaixado, ❌ adminNaoAlteraPapelDeOwner, ❌ memberNaoAlteraPapeis, ❌ adminPromoveMember, ❌ ownerPodeRebaixarOutroOwner, ❌ auditoriaRegistraMudancaDePapel
- **C — Sem knowledge base**: ❌ ultimoOwnerNaoPodeSerRebaixado, ❌ adminNaoAlteraPapelDeOwner, ❌ memberNaoAlteraPapeis, ❌ adminPromoveMember, ❌ ownerPodeRebaixarOutroOwner, ❌ auditoriaRegistraMudancaDePapel

### t5
- **A — Vault estruturado p/ agentes**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **B — Zettelkasten clássico**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ✅ ACTIVE: classe badge-success + rotulo 'Ativo', ✅ INVITED: classe badge-warning + rotulo 'Convite pendente', ✅ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ✅ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **C — Sem knowledge base**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
