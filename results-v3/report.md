# Benchmark de knowledge base — relatório

| Tarefa | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| t1 | 0/6 (0%) ⚠não compilou | 1/6 (17%) | 0/6 (0%) |
| t2 | 1/7 (14%) | 1/7 (14%) | 0/7 (0%) ⚠não compilou |
| t3 | 0/5 (0%) ⚠não compilou | 0/5 (0%) | 0/5 (0%) ⚠não compilou |
| t4 | 5/6 (83%) | 0/6 (0%) ⚠não compilou | 0/6 (0%) ⚠não compilou |
| t5 | 2/7 (29%) | 6/7 (86%) ⚠não compilou | 2/7 (29%) |
| **Total** | 8/31 (26%) | 8/31 (26%) | 2/31 (6%) |

## Retrieval e custo

| Métrica | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| Ações de retrieval (média) | 7.40 | 7.00 | 0.00 |
| Notas lidas (média) | 3.60 | 5.00 | 0.00 |
| Acerto de notas-ouro (média) | 0.40 | 0.93 | — |
| Tokens de prompt (média) | 18436.40 | 22263.20 | 8114.20 |
| Duração por tarefa (s, média) | 102.46 | 110.40 | 169.26 |
| Reparos de compilação (média) | 1.20 | 1.20 | 2.00 |
| Tarefas que compilaram | 0.60 | 0.60 | 0.40 |

## Detalhe por teste

### t1
- **A — Vault estruturado p/ agentes**: sem relatorio surefire (compilacao?)
- **B — Zettelkasten clássico**: ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes, ❌ memberNaoPodeConvidar, ✅ atorDeOutroTenantRecebe404, ❌ conviteExpiraEm72Horas, ❌ adminCriaConvitePersistido
- **C — Sem knowledge base**: ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes, ❌ memberNaoPodeConvidar, ❌ atorDeOutroTenantRecebe404, ❌ conviteExpiraEm72Horas, ❌ adminCriaConvitePersistido

### t2
- **A — Vault estruturado p/ agentes**: ❌ adminNaoPodeDeletarOwner, ❌ purgeAtEm30Dias, ❌ memberNaoPodeDeletar, ❌ auditoriaRegistraSoftDelete, ✅ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ❌ adminFazSoftDelete
- **B — Zettelkasten clássico**: ❌ adminNaoPodeDeletarOwner, ❌ purgeAtEm30Dias, ❌ memberNaoPodeDeletar, ❌ auditoriaRegistraSoftDelete, ✅ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ❌ adminFazSoftDelete
- **C — Sem knowledge base**: sem relatorio surefire (compilacao?)

### t3
- **A — Vault estruturado p/ agentes**: sem relatorio surefire (compilacao?)
- **B — Zettelkasten clássico**: ❌ reenvioIncrementaContadorEResetaExpiracao, ❌ maximoDe3Reenvios, ❌ reenvioReativaConviteExpirado, ❌ memberNaoPodeReenviar, ❌ auditoriaRegistraReenvio
- **C — Sem knowledge base**: sem relatorio surefire (compilacao?)

### t4
- **A — Vault estruturado p/ agentes**: ❌ ultimoOwnerNaoPodeSerRebaixado, ✅ adminNaoAlteraPapelDeOwner, ✅ auditoriaRegistraMudancaDePapel, ✅ memberNaoAlteraPapeis, ✅ adminPromoveMember, ✅ ownerPodeRebaixarOutroOwner
- **B — Zettelkasten clássico**: sem relatorio surefire (compilacao?)
- **C — Sem knowledge base**: sem relatorio surefire (compilacao?)

### t5
- **A — Vault estruturado p/ agentes**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **B — Zettelkasten clássico**: src/app/user-list.component.ts(33,19): error TS2304: Cannot find name 'UserView'.
- **C — Sem knowledge base**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
