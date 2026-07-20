# 202604111600 Frontend status badges

Never show the raw enum to the user. Canonical mapping (CSS class + label).
Careful: the product UI is in Brazilian Portuguese — the labels are exact
strings, do not translate them:

- ACTIVE → `badge-success` / "Ativo"
- INVITED → `badge-warning` / "Convite pendente"
- SUSPENDED → `badge-muted` / "Suspenso"
- DELETED → `badge-danger` / "Excluído"

For DELETED, also show the definitive removal date:
"Remoção definitiva em {purgeAt}" formatted dd/MM/yyyy
(Angular: `{{ user.purgeAt | date:'dd/MM/yyyy' }}`).
The purgeAt comes from soft-delete: [[202603150900-soft-delete-30-days]].

No per-screen color variations — we've already had 3 different greens.
