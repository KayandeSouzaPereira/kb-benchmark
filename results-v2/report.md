# Benchmark de knowledge base — relatório

| Tarefa | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| t1 | 0/6 (não compilou) | 0/6 (não compilou) | 1/6 (17%) |
| t2 | 0/7 (não compilou) | 0/7 (não compilou) | 0/7 (0%) |
| t3 | 0/5 (não compilou) | 0/5 (não compilou) | 0/5 (0%) |
| t4 | 5/6 (83%) | 5/6 (83%) | 0/6 (0%) |
| t5 | 2/7 (29%) | 2/7 (29%) | 2/7 (29%) |
| **Total** | 7/31 (23%) | 7/31 (23%) | 3/31 (10%) |

## Retrieval e custo

| Métrica | A — Vault estruturado p/ agentes | B — Zettelkasten clássico | C — Sem knowledge base |
|---|---|---|---|
| Ações de retrieval (média) | 7.40 | 7.20 | 0.00 |
| Notas lidas (média) | 3.20 | 5.20 | 0.00 |
| Acerto de notas-ouro (média) | 0.47 | 0.93 | — |
| Tokens de prompt (média) | 16927.60 | 24161.80 | 2530.40 |
| Duração por tarefa (s, média) | 104.50 | 140.00 | 91.96 |
| Reparos de compilação (média) | 1.20 | 1.20 | 0.60 |
| Tarefas que compilaram | 0.40 | 0.40 | 1.00 |

## Detalhe por teste

### t1
- **A — Vault estruturado p/ agentes**: sem relatorio surefire (compilacao?)
- **B — Zettelkasten clássico**: sem relatorio surefire (compilacao?)
- **C — Sem knowledge base**: ❌ auditoriaRegistraUserInvited, ❌ limiteDoPlanoFreeContaConvitesPendentes, ❌ memberNaoPodeConvidar, ✅ atorDeOutroTenantRecebe404, ❌ conviteExpiraEm72Horas, ❌ adminCriaConvitePersistido

### t2
- **A — Vault estruturado p/ agentes**: sem relatorio surefire (compilacao?)
- **B — Zettelkasten clássico**: sem relatorio surefire (compilacao?)
- **C — Sem knowledge base**: ❌ adminNaoPodeDeletarOwner, ❌ purgeAtEm30Dias, ❌ memberNaoPodeDeletar, ❌ auditoriaRegistraSoftDelete, ❌ atorDeOutroTenantRecebe404, ❌ ninguemDeletaASiMesmo, ❌ adminFazSoftDelete

### t3
- **A — Vault estruturado p/ agentes**: sem relatorio surefire (compilacao?)
- **B — Zettelkasten clássico**: sem relatorio surefire (compilacao?)
- **C — Sem knowledge base**: ❌ reenvioIncrementaContadorEResetaExpiracao, ❌ maximoDe3Reenvios, ❌ reenvioReativaConviteExpirado, ❌ memberNaoPodeReenviar, ❌ auditoriaRegistraReenvio

### t4
- **A — Vault estruturado p/ agentes**: ❌ ultimoOwnerNaoPodeSerRebaixado, ✅ adminNaoAlteraPapelDeOwner, ✅ auditoriaRegistraMudancaDePapel, ✅ memberNaoAlteraPapeis, ✅ adminPromoveMember, ✅ ownerPodeRebaixarOutroOwner
- **B — Zettelkasten clássico**: ❌ ultimoOwnerNaoPodeSerRebaixado, ✅ adminNaoAlteraPapelDeOwner, ✅ auditoriaRegistraMudancaDePapel, ✅ memberNaoAlteraPapeis, ✅ adminPromoveMember, ✅ ownerPodeRebaixarOutroOwner
- **C — Sem knowledge base**: ❌ ultimoOwnerNaoPodeSerRebaixado, ❌ adminNaoAlteraPapelDeOwner, ❌ auditoriaRegistraMudancaDePapel, ❌ memberNaoAlteraPapeis, ❌ adminPromoveMember, ❌ ownerPodeRebaixarOutroOwner

### t5
- **A — Vault estruturado p/ agentes**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **B — Zettelkasten clássico**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
- **C — Sem knowledge base**: ✅ arquivo src/app/user-list.component.ts existe, ✅ type-check (tsc --noEmit) passa, ❌ ACTIVE: classe badge-success + rotulo 'Ativo', ❌ INVITED: classe badge-warning + rotulo 'Convite pendente', ❌ SUSPENDED: classe badge-muted + rotulo 'Suspenso', ❌ DELETED: classe badge-danger + rotulo 'Excluído', ❌ DELETED: exibe purgeAt no formato dd/MM/yyyy
