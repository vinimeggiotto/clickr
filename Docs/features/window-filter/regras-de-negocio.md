# Feature: Filtro de janela

## Objetivo

Só emitir clique quando a janela em foco atender aos critérios configurados.

## Configuração (`window_filter`)

| Campo | Tipo | Papel |
|-------|------|--------|
| `enabled` | bool | Liga/desliga a regra |
| `process` | string | Nome do executável (ex.: `notepad` ou `notepad.exe`) |
| `title_contains` | string | Substring no título da janela (case-insensitive) |

## Comportamento

1. `enabled = false` → todos os cliques permitidos.
2. `enabled = true` sem `process` nem `title_contains` → permitido (sem critério ativo).
3. Critérios não vazios são **AND**: processo (se informado) e título (se informado) devem casar.
4. `allows() == false` → o motor **pula** o clique (não é contingência; é a regra do filtro).
5. Identificação via janela em foreground (`GetForegroundWindow` + título + nome do processo).

## Regras

- Processo: comparação case-insensitive; aceita com ou sem sufixo `.exe`.
- Falha ao obter processo/título com filtro ativo e critério correspondente → não permite o clique.
- Sem retry nem “clicar em outra janela”.
