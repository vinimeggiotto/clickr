# Feature: Mouse 4 / 5 (XBUTTON)

## Objetivo

Permitir cliques com os botões laterais do mouse.

## Comportamento

| Valor `button` | Windows (SendInput) | macOS / Linux (pynput) |
|----------------|---------------------|-------------------------|
| `x1` | `MOUSEEVENTF_XDOWN/UP` + `XBUTTON1` | `Button.x1` se existir no enum |
| `x2` | `MOUSEEVENTF_XDOWN/UP` + `XBUTTON2` | `Button.x2` se existir no enum |

- Mesmos modos que L/R/M: simples, duplo, hold, cursor, ponto fixo, sequência, burst.
- UI: seletor compacto `L R M 4 5` no device.
- Fora do Windows, se o backend não expuser X1/X2 → `OSError` explícito (sem mapear para outro botão).

## Regras

- No Win32, `mouseData` obrigatório nos eventos X; botões clássicos usam `mouseData = 0`.
- Botão inválido na config é normalizado para `left` no parse.
