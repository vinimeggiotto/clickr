# DOC — core/sendinput.py

## Objetivo

Encapsular a API Win32 `SendInput` / `GetCursorPos` / `GetSystemMetrics` via `ctypes` para mouse (incl. XBUTTON1/2) e teclado (VK).

## Dependências

- `ctypes` / `ctypes.wintypes` (stdlib)
- `user32.dll` (Windows)

## Lógica central

- Coordenadas de ponto fixo usam tela virtual (`SM_*VIRTUALSCREEN`) normalizadas para o intervalo SendInput **0–65535**, com flags `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK`.
- Clique no cursor: apenas `DOWN` + `UP` do botão escolhido, sem mover.
- Botões `x1`/`x2` usam `MOUSEEVENTF_XDOWN/XUP` com `mouseData` = `XBUTTON1`/`XBUTTON2`.
- Teclado: `INPUT_KEYBOARD` + VK via `name_to_vk` / `key_down` / `key_up` / `key_press`.
- Falha de `SendInput` (retorno ≠ quantidade enviada) levanta `OSError` com código Win32.

## Assinaturas

| Função | Entrada | Saída / efeito |
|--------|---------|----------------|
| `get_cursor_pos()` | — | `(x, y)` pixels |
| `get_virtual_screen_rect()` | — | `(x, y, width, height)` tela virtual |
| `move_absolute(x, y)` | pixels tela virtual | move cursor |
| `click(button)` | `left\|right\|middle\|x1\|x2` | clique no cursor |
| `click_at(button, x, y)` | botão + XY | move + clique |
| `double_click(button)` | botão | dois cliques no cursor |
| `double_click_at(button, x, y)` | botão + XY | dois cliques no ponto |
| `button_down(button)` / `button_up(button)` | botão | pressionar / soltar |
| `name_to_vk(name)` | nome tecla | VK int |
| `key_down` / `key_up` / `key_press` | VK | teclado |
| `key_*_name(name)` | nome | teclado por nome |
| `button_from_pynput(button)` | botão pynput | `ButtonName` ou `None` |
