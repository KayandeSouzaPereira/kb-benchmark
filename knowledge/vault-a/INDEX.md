# INDEX — Base de conhecimento do time (SaaS de gestão de usuários)

Leia este arquivo primeiro. Ele mapeia o que existe em cada pasta e quando consultar.

| Pasta | Conteúdo | Quando consultar |
|---|---|---|
| `dominio/` | Regras de negócio do produto: papéis e permissões, limites de plano, convites, exclusão de usuários, auditoria, autenticação | Antes de implementar QUALQUER endpoint ou tela que mexa com usuários, convites ou papéis |
| `padroes-codigo/` | Convenções técnicas do time: formato de erros da API, badges de status no frontend | Sempre que for retornar erro HTTP ou renderizar status na UI |
| `decisoes/` | ADRs — decisões arquiteturais com alternativas descartadas | Quando uma regra parecer estranha ou você quiser propor algo diferente |
| `produto/` | Material de produto: planos e preços | Contexto comercial; raramente necessário para código |
| `runbooks/` | Procedimentos operacionais (deploy etc.) | Operação, não desenvolvimento |

## Arquivos por pasta

- `dominio/papeis-e-permissoes.md` — hierarquia OWNER/ADMIN/MEMBER, quem pode fazer o quê, proteções do owner
- `dominio/limites-de-plano.md` — quantos usuários cada plano permite e o que conta no limite
- `dominio/convites.md` — ciclo de vida do convite: expiração, reenvio, aceitação
- `dominio/exclusao-de-usuarios.md` — soft-delete, retenção, quem pode excluir
- `dominio/auditoria.md` — o que auditar e formato obrigatório do AuditEntry
- `dominio/autenticacao-e-lockout.md` — política de senha e bloqueio de conta
- `padroes-codigo/formato-de-erros-api.md` — envelope JSON de erro + tabela de códigos e status HTTP
- `padroes-codigo/badges-de-status-frontend.md` — classes CSS e rótulos PT-BR por status de usuário
- `decisoes/adr-001-soft-delete-com-retencao.md` — por que nunca há hard delete
- `decisoes/adr-002-convites-pendentes-contam-no-limite.md` — por que convite pendente ocupa vaga
- `produto/planos-e-precos.md` — Free / Pro / Enterprise
- `runbooks/deploy-producao.md` — pipeline de deploy
