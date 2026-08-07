# Feature: Script DSL

## Objetivo

Executar uma mini-linguagem de ações (`click`, `move`, `wait`, `key`, loops limitados) via SendInput.

## Gramática (por linha)

| Comando | Forma |
|---------|--------|
| `click` | `click` \| `click BUTTON` \| `click X Y` \| `click BUTTON X Y` |
| `move` | `move X Y` |
| `wait` | `wait MS` |
| `key` | `key NOME` (ex: `A`, `F6`, `SPACE`) |
| `loop` | `loop N` … `end` |

Comentários: linhas `# ...` ou vazias.

## Limites

- Máx. 500 linhas
- Loop: N entre 1 e 1000
- Profundidade de loop ≤ 2
- Botões: `left`, `right`, `middle`, `x1`, `x2`

## Comportamento

1. Parse falha → erro em `last_error`, não inicia thread.
2. Execução em thread dedicada; `script_stop` ou hotkey interrompe.
3. Motor e macro são parados ao iniciar script.

## Bridge

`script_run(source)` / `script_stop()`. Estado: `get_state().script` → `running`, `line`.

## UI

Aba **Script** com textarea (oculta no modo compacto).
