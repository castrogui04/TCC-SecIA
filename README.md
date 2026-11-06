# Experimento – Análise de segurança de código gerado por LLMs

> **Este repositório contém código gerado por IA com vulnerabilidades identificadas para fins de pesquisa. Não utilize em produção.**

## Estrutura

```
experimento/            # 3 modelos x 3 execuções (E1-E3) x 5 etapas (T1-T5) = 45 pastas
  GPT/    E1/E2/E3/T1..T5
  Claude/ E1/E2/E3/T1..T5
  Gemini/ E1/E2/E3/T1..T5
piloto/                 # execução piloto (calibração)
prompts/                # prompts usados em cada etapa
planilha/               # planilhas de consolidação dos resultados
scripts/                # analisar.sh
teste_ferramentas/      # app vulnerável usado para validar as ferramentas
versoes_ambiente.txt    # registro de versões e configurações
```

## Ferramentas

Instaladas em `.venv-ferramentas` (não versionado):

| Ferramenta | Versão |
|------------|--------|
| Semgrep    | 1.184.0 |
| Bandit     | 1.9.4  |
| Python     | 3.13.11 |

Regras do Semgrep: `p/python` + `p/flask`.

## Uso

```bash
./scripts/analisar.sh experimento/GPT/E1/T1
```

Gera `semgrep.json` e `bandit.json` dentro da pasta analisada e imprime a
contagem de resultados de cada ferramenta. O script não modifica código.

## Preparação do ambiente

```bash
python3 -m venv .venv-ferramentas
source .venv-ferramentas/bin/activate
pip install semgrep bandit
```
