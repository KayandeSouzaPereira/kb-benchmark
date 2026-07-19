---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-03-10
---

# Autenticação e lockout

## Política de senha

- Mínimo 12 caracteres, pelo menos 1 número e 1 símbolo.
- Histórico: as 5 últimas senhas não podem ser reutilizadas.

## Lockout

- 5 tentativas de login falhas consecutivas bloqueiam a conta por 15 minutos.
- O contador zera após login bem-sucedido ou expiração do bloqueio.
- Desbloqueio manual por ADMIN+ é permitido e gera auditoria.

## Relacionados

- [papeis-e-permissoes](papeis-e-permissoes.md)
- [auditoria](auditoria.md)
