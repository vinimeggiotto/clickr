# Feature: Mouse 4 / 5 (XBUTTON)

## Objetivo

Permitir cliques com os botões laterais do mouse via SendInput.

## Comportamento

| Valor `button` | Win32 |
|----------------|--------|
| `x1` | `MOUSEEVENTF_XDOWN/UP` + `XBUTTON1` |
| `x2` | `MOUSEEVENTF_XDOWN/UP` + `XBUTTON2` |

- Mesmos modos que L/R/M: simples, duplo, hold, cursor, ponto fixo, sequência, burst.
- UI: seletor compacto `L R M 4 5` no device.

## Regras

- `mouseData` obrigatório nos eventos X; botões clássicos usam `mouseData = 0`.
- Botão inválido na config é normalizado para `left` no parse.
