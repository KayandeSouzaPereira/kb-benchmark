# 202604111600 Badges de status no front

Nunca mostrar o enum cru para o usuário. Mapeamento canônico
(classe CSS + rótulo PT-BR):

- ACTIVE → `badge-success` / "Ativo"
- INVITED → `badge-warning` / "Convite pendente"
- SUSPENDED → `badge-muted` / "Suspenso"
- DELETED → `badge-danger` / "Excluído"

Para DELETED, mostrar junto a data de remoção definitiva:
"Remoção definitiva em {purgeAt}" no formato dd/MM/yyyy
(Angular: `{{ user.purgeAt | date:'dd/MM/yyyy' }}`).
O purgeAt vem do soft-delete: [[202603150900-soft-delete-30-dias]].

Nada de variação de cor por tela — já tivemos 3 verdes diferentes.
