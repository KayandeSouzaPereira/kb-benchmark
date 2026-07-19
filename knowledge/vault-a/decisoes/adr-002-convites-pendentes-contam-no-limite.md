---
tipo: adr
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# ADR-002 — Convites pendentes contam no limite de assentos do plano

## Decisão

`assentos ocupados = usuários não-DELETED + convites PENDING`. Vale para toda
verificação de limite de plano.

## Contexto

Sem isso, um tenant FREE convidava 30 pessoas e todas conseguiam aceitar,
estourando o plano. Billing e produto decidiram em 2026-05-02 que a vaga é
reservada no momento do convite.

## Alternativas descartadas — não propor novamente

- **Contar só usuários ativos**: permite estourar o plano via convites em massa
  (bug real do incidente #482).
- **Bloquear na aceitação**: péssima UX — a pessoa clica no e-mail e descobre
  que não há vaga.

## Relacionados

- [../dominio/limites-de-plano.md](../dominio/limites-de-plano.md)
- [../dominio/convites.md](../dominio/convites.md)
