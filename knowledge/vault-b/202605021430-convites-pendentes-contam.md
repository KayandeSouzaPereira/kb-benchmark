# 202605021430 Correção: convites pendentes CONTAM no limite

Decisão final com billing e produto (reunião de 2026-05-02), corrigindo
minha intuição de [[202603121015-convites-e-limite-duvida]]:

**assentos ocupados = usuários com status != DELETED + convites PENDING.**

A vaga é reservada no momento do convite. Motivo: sem isso, um tenant FREE
convidava 30 pessoas e todas aceitavam (bug do incidente #482). Bloquear na
aceitação seria UX horrível.

Consequência prática: criar convite quando ocupados >= máximo do plano →
422 `PLAN_LIMIT_EXCEEDED` ([[202601121000-limites-por-plano]]).
Reenvio NÃO passa por essa checagem — não cria assento novo
([[202602041130-reenvio-de-convites]]).
