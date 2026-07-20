# Benchmark de knowledge base — relatório

| Tarefa | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| t1 | 1/6 (17%) | 1/6 (17%) | 0/6 (0%) |
| t2 | 3/7 (43%) | 1/7 (14%) | 2/7 (29%) |
| t3 | 5/5 (100%) | 5/5 (100%) | 0/5 (0%) |
| t4 | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) |
| t5 | 2/7 (29%) | 5/7 (71%) | 2/7 (29%) |
| **Total** | 11/31 (35%) | 12/31 (39%) | 4/31 (13%) |

## Retrieval e custo

| Métrica | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| Ações de retrieval (média) | 7.20 | 6.80 | 0.00 |
| Notas lidas (média) | 2.60 | 4.80 | 0.00 |
| Acerto de notas-ouro (média) | 0.43 | 0.87 | — |
| Tokens de prompt (média) | 20406.40 | 28729.80 | 721.00 |
| Duração por tarefa (s, média) | 185.56 | 253.62 | 77.48 |
| Reparos de compilação (média) | 0.20 | 0.40 | 0.00 |
| Tarefas que compilaram | 1.00 | 1.00 | 1.00 |

## Detalhe por teste

### t1
- **A — Vault estruturado p/ agentes**: ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes, ❌ memberNaoPodeConvidar, ❌ atorDeOutroTenantRecebe404, ❌ conviteExpiraEm72Horas, ✅ adminCriaConvitePersistido
- **B — Zettelkasten clássico**: ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes, ❌ memberNaoPodeConvidar, ✅ atorDeOutroTenantRecebe404, ❌ conviteExpiraEm72Horas, ❌ adminCriaConvitePersistido
- **C — Sem knowledge base**: ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes, ❌ memberNaoPodeConvidar, ❌ atorDeOutroTenantRecebe404, ❌ conviteExpiraEm72Horas, ❌ adminCriaConvitePersistido

### t2
- **A — Vault estruturado p/ agentes**: ❌ adminNaoPodeDeletarOwner, ✅ purgeAtEm30Dias, ❌ memberNaoPodeDeletar, ✅ auditoriaRegistraSoftDelete, ❌ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ✅ adminFazSoftDelete
- **B — Zettelkasten clássico**: ❌ adminNaoPodeDeletarOwner, ❌ purgeAtEm30Dias, ❌ memberNaoPodeDeletar, ❌ auditoriaRegistraSoftDelete, ✅ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ❌ adminFazSoftDelete
- **C — Sem knowledge base**: ❌ adminNaoPodeDeletarOwner, ✅ purgeAtEm30Dias, ❌ memberNaoPodeDeletar, ❌ auditoriaRegistraSoftDelete, ❌ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ✅ adminFazSoftDelete

### t3
- **A — Vault estruturado p/ agentes**: ✅ reenvioIncrementaContadorEResetaExpiracao, ✅ maximoDe3Reenvios, ✅ reenvioReativaConviteExpirado, ✅ memberNaoPodeReenviar, ✅ auditoriaRegistraReenvio
- **B — Zettelkasten clássico**: ✅ reenvioIncrementaContadorEResetaExpiracao, ✅ maximoDe3Reenvios, ✅ reenvioReativaConviteExpirado, ✅ memberNaoPodeReenviar, ✅ auditoriaRegistraReenvio
- **C — Sem knowledge base**: ❌ reenvioIncrementaContadorEResetaExpiracao, ❌ maximoDe3Reenvios, ❌ reenvioReativaConviteExpirado, ❌ memberNaoPodeReenviar, ❌ auditoriaRegistraReenvio

### t4
- **A — Vault estruturado p/ agentes**: ❌ ultimoOwnerNaoPodeSerRebaixado, ❌ adminNaoAlteraPapelDeOwner, ❌ auditoriaRegistraMudancaDePapel, ❌ memberNaoAlteraPapeis, ❌ adminPromoveMember, ❌ ownerPodeRebaixarOutroOwner
- **B — Zettelkasten clássico**: ❌ ultimoOwnerNaoPodeSerRebaixado, ❌ adminNaoAlteraPapelDeOwner, ❌ auditoriaRegistraMudancaDePapel, ❌ memberNaoAlteraPapeis, ❌ adminPromoveMember, ❌ ownerPodeRebaixarOutroOwner
- **C — Sem knowledge base**: ❌ ultimoOwnerNaoPodeSerRebaixado, ❌ adminNaoAlteraPapelDeOwner, ❌ auditoriaRegistraMudancaDePapel, ❌ memberNaoAlteraPapeis, ❌ adminPromoveMember, ❌ ownerPodeRebaixarOutroOwner

### t5
- **A — Vault estruturado p/ agentes**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **B — Zettelkasten clássico**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ✅ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ✅ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ✅ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **C — Sem knowledge base**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
