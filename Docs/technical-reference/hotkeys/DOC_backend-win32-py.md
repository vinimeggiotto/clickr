# DOC — hotkeys/backend_win32.py

## Objetivo

Registrar os atalhos globais no Windows com `RegisterHotKey`, de modo que a combinação seja consumida pelo sistema e não chegue ao programa em foco.

## Dependências

- `ctypes` / `user32` (`RegisterHotKey`, `UnregisterHotKey`, `GetMessageW`, `PeekMessageW`, `PostThreadMessageW`, `GetAsyncKeyState`), `kernel32`
- `hotkeys.backend_pynput.PynputHotkeyBackend` (reserva)
- `hotkeys.combo.Combo`, `app.log`

## Lógica central

- Uma thread dedicada (`HotkeysWin32`) cria a própria fila de mensagens e roda o loop `GetMessageW`; os registros são feitos **nessa** thread (exigência da API).
- `apply(bindings)` guarda os combos desejados e posta `WM_APP_APPLY`; a thread então desregistra tudo e registra de novo, com `MOD_NOREPEAT` (sem auto-repetição).
- `WM_HOTKEY` → `on_action(ação)`.
- Combo que o Windows recusa (já usado por outro programa ou reservado) vai para o backend pynput de reserva, iniciado sob demanda; `apply` devolve `{ação: combo}` dos que estão na reserva.
- `pause()` / `resume()` desregistram / registram novamente (usado durante a captura de atalho) e repassam à reserva.
- `is_pressed(combo)`: `GetAsyncKeyState` da tecla principal.
- `stop()` posta `WM_QUIT`, aguarda a thread e para a reserva.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `Win32HotkeyBackend(on_action)` | callback `(str) -> None` | instância |
| `start()` / `stop()` | — | thread de mensagens |
| `apply(bindings)` | `dict[str, Combo]` | `dict[str, str]` (ações na reserva pynput) |
| `pause()` / `resume()` | — | suspende / retoma os atalhos |
| `is_pressed(combo)` | `Combo` | `bool` |
