# Feature: Filtro de janela

## Objetivo

Só emitir clique quando a janela em foco atender aos critérios configurados.

## Configuração (`window_filter`)

| Campo | Tipo | Papel |
|-------|------|--------|
| `enabled` | bool | Liga/desliga a regra |
| `process` | string | Nome do executável / app / WM_CLASS (ex.: `notepad`, `Safari`, `firefox`) |
| `title_contains` | string | Substring no título da janela (case-insensitive) |

## Comportamento

1. `enabled = false` → todos os cliques permitidos.
2. `enabled = true` sem `process` nem `title_contains` → permitido (sem critério ativo).
3. Critérios não vazios são **AND**: processo (se informado) e título (se informado) devem casar.
4. `allows() == false` → o motor **pula** o clique (não é contingência; é a regra do filtro).
5. Identificação da janela em foreground:

| SO | Mecanismo |
|----|-----------|
| Windows | `GetForegroundWindow` + título + basename do exe |
| macOS | `osascript` / System Events (nome do app + título da janela) |
| Linux | `xprop` (`_NET_ACTIVE_WINDOW`, `WM_CLASS`, nome); `xdotool` opcional para título |

## Regras

- Processo: comparação case-insensitive; no Windows aceita com ou sem sufixo `.exe`.
- Falha ao obter processo/título com filtro ativo e critério correspondente → não permite o clique.
- Ferramenta ausente no Linux (`xprop`) ou macOS (`osascript`) com filtro ativo e critérios → **erro explícito** (`OSError`), sem liberar o clique.
- Sem retry nem “clicar em outra janela”.
