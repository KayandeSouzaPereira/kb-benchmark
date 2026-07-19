# 202602041130 Reenvio de convites

Reenvio é ADMIN+, como toda mutação ([[202601051030-papeis-do-tenant]]).

- **Máximo 3 reenvios por convite.** O 4º → 422 `RESEND_LIMIT_REACHED`,
  sem alterar nada. (Anti-spam: reclamação de destinatários bombardeados.)
- Cada reenvio incrementa `resendCount` e **reseta `expiresAt` para agora
  + 72h** — a janela de [[202602041100-expiracao-de-convites-72h]] recomeça.
- Reenviar convite já expirado é permitido e o **reativa** (nova janela).
  Não faz sentido obrigar a recriar o convite.
- Reenvio NÃO passa pela checagem de limite de plano — o assento já está
  reservado ([[202605021430-convites-pendentes-contam]]).
- Audita `INVITATION_RESENT` ([[202601201300-auditoria-de-mutacoes]]).
