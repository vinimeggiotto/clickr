# DOC — hotkeys/service.py

## Objetivo

Registrar hotkey global de toggle e permitir gravação da tecla via captura do próximo press.

## Dependências

- `pynput.keyboard`

## Lógica central

- `resolve_key` / `format_key` normalizam nomes (`F6`, `A`, `SPACE`, …).
- Listener principal chama `on_toggle` quando a tecla atual é pressionada (ignorado se `recording`).
- `begin_capture` sobe um listener temporário; na primeira tecla válida chama o callback e encerra a captura.
- `set_hotkey` atualiza o alvo sem reiniciar o listener principal.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `HotkeyService(on_toggle, hotkey="F6")` | callback, nome | instância |
| `start()` / `stop()` | — | ciclo do listener |
| `set_hotkey(name)` | str | nome normalizado |
| `begin_capture(on_captured)` | callback `(str) -> None` | — |
| `cancel_capture()` | — | cancela gravação |
| `format_key(key)` / `resolve_key(name)` | tecla / nome | str / KeyLike |
| `hotkey` / `recording` | — | propriedades |
