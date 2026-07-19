# 202601080800 Lockout e política de senhas

Senha: mínimo 12 caracteres, 1 número, 1 símbolo; últimas 5 não reutilizáveis.

Lockout: 5 falhas consecutivas de login → bloqueio de 15 minutos. Contador
zera com login ok ou expiração. ADMIN+ pode desbloquear manualmente (com
auditoria — [[202601201300-auditoria-de-mutacoes]]).

Nota: isso é autenticação, não gestão de usuários; mantive separado do mapa
[[202601050900-mapa-dominio-usuarios]].
