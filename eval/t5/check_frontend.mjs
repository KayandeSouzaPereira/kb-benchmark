// Avalia a tarefa t5 (Angular): type-check + verificacoes estaticas das
// convencoes de badge do time. Uso: node check_frontend.mjs <workspace>
import { execSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const ws = process.argv[2];
if (!ws) {
  console.error('uso: node check_frontend.mjs <workspace>');
  process.exit(2);
}

const results = [];
const check = (name, ok) => results.push({ name, passed: !!ok });

const compPath = join(ws, 'src', 'app', 'user-list.component.ts');
const exists = existsSync(compPath);
check('arquivo src/app/user-list.component.ts existe', exists);

// concatena .ts + templates/estilos separados (templateUrl é aceitavel)
let src = '';
if (exists) src = readFileSync(compPath, 'utf8');
for (const extra of ['user-list.component.html', 'user-list.component.css']) {
  const p = join(ws, 'src', 'app', extra);
  if (existsSync(p)) src += '\n' + readFileSync(p, 'utf8');
}

let tscOk = false;
let tscOut = '';
if (exists) {
  try {
    execSync('node node_modules/typescript/lib/tsc.js -p tsconfig.json --noEmit',
      { cwd: ws, stdio: 'pipe' });
    tscOk = true;
  } catch (e) {
    tscOut = [e.stdout, e.stderr, e.message].map(String).join('\n').slice(0, 2500);
  }
}
check('type-check (tsc --noEmit) passa', tscOk);

check("ACTIVE: classe badge-success + rotulo 'Ativo'",
  src.includes('badge-success') && src.includes('Ativo'));
check("INVITED: classe badge-warning + rotulo 'Convite pendente'",
  src.includes('badge-warning') && src.includes('Convite pendente'));
check("SUSPENDED: classe badge-muted + rotulo 'Suspenso'",
  src.includes('badge-muted') && src.includes('Suspenso'));
check("DELETED: classe badge-danger + rotulo 'Excluído'",
  src.includes('badge-danger') && src.includes('Excluído'));
check("DELETED: exibe purgeAt no formato dd/MM/yyyy",
  src.includes('purgeAt') && src.includes('dd/MM/yyyy'));

console.log(JSON.stringify({
  results,
  tsc_output: tscOut,
}));
