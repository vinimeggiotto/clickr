# DOC — core/sendinput_win32.py

## Objetivo

Implementar a API de input no Windows via Win32 `SendInput` / `GetCursorPos` / `GetSystemMetrics`.

## Dependências

- `ctypes` / `ctypes.wintypes`
- `user32.dll` (`SendInput`, `GetCursorPos`, `GetSystemMetrics`, `MapVirtualKeyW`)
- `core.keys.name_to_vk`

## Lógica central

- Clique no cursor: `DOWN` + `UP` sem mover.
- Ponto fixo (`click_at`): **um único lote** `SendInput` com movimento absoluto na tela virtual + `count` pares down/up; com `restore=True` o lote termina com o movimento de volta à posição lida antes do envio.
- `x1`/`x2`: `MOUSEEVENTF_XDOWN/XUP` com `mouseData` = `XBUTTON1`/`XBUTTON2`.
- Rolagem: `MOUSEEVENTF_WHEEL` (vertical) e `MOUSEEVENTF_HWHEEL` (horizontal), `WHEEL_DELTA = 120` por "clique".
- Teclado por VK: `INPUT_KEYBOARD` com VK + scancode (`MapVirtualKeyW`); teclas de `_EXTENDED_VKS` (navegação, Insert/Delete, Win, Menu, divisão do numpad, NumLock, Ctrl/Alt direitos) recebem `KEYEVENTF_EXTENDEDKEY`.
- Teclado por caractere / `type_text`: `KEYEVENTF_UNICODE`, uma entrada por unidade UTF-16 (independe do layout).

## Assinaturas

Mesma superfície pública reexportada por `core.sendinput` (ver `DOC_sendinput-py.md`).
