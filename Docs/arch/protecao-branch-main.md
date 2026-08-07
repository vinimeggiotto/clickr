# Proteção da branch `main` (documentação)

## Importante

O arquivo [`github-ruleset-main.json`](github-ruleset-main.json) é **apenas documentação / template**.

O GitHub **não** aplica ruleset automaticamente só porque o JSON está no repositório. A proteção real fica em **Settings → Rules → Rulesets** (ou via API).

## Intenção

- Repo público: issues, fork, branch no fork e PR
- `main`: só via pull request (sem push direto / force push / delete)
- Checks do workflow Build (matrix Windows / macOS / Linux) antes do merge
- Admin pode bypass **apenas no fluxo de PR** (`bypass_mode: pull_request`)

## Como aplicar

```powershell
gh api -X POST repos/vinimeggiotto/clickr/rulesets --input Docs/arch/github-ruleset-main.json
```

Ou: GitHub → **Settings → Rules → New branch ruleset** e espelhar o JSON.

## Ajustes

- Os `context` dos status checks precisam bater com os nomes exatos nos Checks de um PR. Se a matrix mudar, atualize o JSON e o ruleset no GitHub.
- Para desativar: UI, ou `enforcement: "disabled"` via API, ou delete do ruleset.
- Editar o JSON no repo **não** atualiza o ruleset ativo até reaplicar na API/UI.
