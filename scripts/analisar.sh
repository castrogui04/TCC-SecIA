#!/usr/bin/env bash
# analisar.sh - executa Semgrep e Bandit sobre uma pasta de implementacao.
#
# Uso:  scripts/analisar.sh <pasta-de-implementacao>
# Ex.:  ./scripts/analisar.sh experimento/GPT/E1/T1
#
# Saidas:
#   <pasta>/semgrep.json
#   <pasta>/bandit.json
#
# O script NAO altera nenhum arquivo de codigo da pasta analisada: apenas
# grava os dois relatorios JSON acima.

set -uo pipefail

LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$LAB/.venv-ferramentas"

if [ "$#" -ne 1 ]; then
  echo "uso: $0 <pasta-de-implementacao>" >&2
  echo "ex.: $0 experimento/GPT/E1/T1" >&2
  exit 2
fi

ALVO="$1"

if [ ! -d "$ALVO" ]; then
  echo "ERRO: pasta nao encontrada: $ALVO" >&2
  exit 2
fi

# caminho absoluto normalizado (sem alterar a pasta)
ALVO="$(cd "$ALVO" && pwd)"

if [ ! -x "$VENV/bin/semgrep" ] || [ ! -x "$VENV/bin/bandit" ]; then
  echo "ERRO: ferramentas ausentes em $VENV" >&2
  exit 3
fi

# ativa o ambiente virtual das ferramentas
# shellcheck disable=SC1091
source "$VENV/bin/activate"

SEMGREP_OUT="$ALVO/semgrep.json"
BANDIT_OUT="$ALVO/bandit.json"

echo "== Alvo: $ALVO"
echo "== Semgrep $(semgrep --version 2>/dev/null) | Bandit $(bandit --version 2>/dev/null | head -1)"

# ---------------------------------------------------------------- Semgrep ---
echo
echo "== [1/2] Semgrep (p/python + p/flask)"
semgrep scan --config p/python --config p/flask --json \
  --output "$SEMGREP_OUT" "$ALVO"
SG_RC=$?
if [ "$SG_RC" -ne 0 ]; then
  echo "AVISO: semgrep retornou codigo $SG_RC" >&2
fi

# ----------------------------------------------------------------- Bandit ---
# Bandit retorna 1 quando encontra problemas: isso e esperado, nao e erro.
echo
echo "== [2/2] Bandit"
bandit -r "$ALVO" -f json -o "$BANDIT_OUT" -x "$ALVO/.venv"
BD_RC=$?
case "$BD_RC" in
  0) echo "   (bandit: nenhum problema)" ;;
  1) echo "   (bandit: problemas encontrados - codigo 1, esperado)" ;;
  *) echo "AVISO: bandit retornou codigo $BD_RC" >&2 ;;
esac

# ------------------------------------------------------------- Contagem -----
echo
echo "== Contagem de resultados"
"$VENV/bin/python" - "$SEMGREP_OUT" "$BANDIT_OUT" <<'PYEOF'
import json, os, sys

def carrega(p):
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        return []
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("results", []) or []
    except Exception as e:
        print(f"   ! falha ao ler {os.path.basename(p)}: {e}")
        return []

sg_path, bd_path = sys.argv[1], sys.argv[2]
sg, bd = carrega(sg_path), carrega(bd_path)

print(f"   semgrep.json : {len(sg)} resultado(s)")
print(f"   bandit.json  : {len(bd)} resultado(s)")

if sg:
    print("\n   -- Semgrep (regra @ arquivo:linha)")
    for r in sg[:20]:
        print(f"      {r.get('check_id','?').split('.')[-1]:<38} "
              f"{os.path.relpath(r.get('path','?'), os.path.dirname(sg_path))}"
              f":{r.get('start',{}).get('line','?')}")
    if len(sg) > 20:
        print(f"      ... (+{len(sg)-20})")

if bd:
    print("\n   -- Bandit (teste / severidade @ arquivo:linha)")
    for r in bd[:20]:
        print(f"      {r.get('test_id','?'):<6} {r.get('issue_severity','?'):<9} "
              f"{os.path.relpath(r.get('filename','?'), os.path.dirname(bd_path))}"
              f":{r.get('line_number','?')}  {r.get('test_name','')}")
    if len(bd) > 20:
        print(f"      ... (+{len(bd)-20})")

sys.exit(0 if (sg or bd) else 0)
PYEOF

echo
echo "== OK: $SEMGREP_OUT"
echo "== OK: $BANDIT_OUT"
exit 0
