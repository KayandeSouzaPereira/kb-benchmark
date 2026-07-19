# 202602101415 Proteção do owner

Percebi hoje discutindo o incidente do cliente Vetrix: se um ADMIN pode
rebaixar ou excluir um OWNER, um admin malicioso toma o tenant.

Regra que fechamos: **ADMIN nunca altera nem exclui um OWNER** — nem papel,
nem exclusão. Resposta: 403 `OWNER_PROTECTED`. Só um OWNER mexe em outro
OWNER, e só um OWNER promove alguém a OWNER.

Isso conecta com o caso extremo do último owner: [[202602101430-ultimo-owner]].
Papéis em geral: [[202601051030-papeis-do-tenant]].
