# 202602151100 Isolamento de tenant responde 404, não 403

O ator (vem no header `X-Actor-Id`) tem que pertencer ao tenant da URL.

Detalhe que quase erramos: quando o ator é de OUTRO tenant, a resposta é
**404 `NOT_FOUND`**, não 403. Um 403 confirmaria para um estranho que o
recurso existe — vazamento de informação. 404 não conta nada.

Vale para todos os endpoints de usuários e convites.
Papéis: [[202601051030-papeis-do-tenant]].
Códigos: [[202601201330-codigos-de-erro-da-api]].
