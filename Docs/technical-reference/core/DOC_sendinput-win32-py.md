# DOC — core/sendinput_win32.py

## Objetivo

Implementar a API de input no Windows via Win32 `SendInput` / `GetCursorPos` / `GetSystemMetrics`.

## Dependências

- `ctypes` / `ctypes.wintypes`
- `user32.dll`

## Lógica central

- Clique no cursor: `DOWN` + `UP` sem mover.
- Ponto fixo: move absoluto na tela virtual + clique.
- `x1`/`x2`: `MOUSEEVENTF_XDOWN/XUP` com `mouseData` = `XBUTTON1`/`XBUTTON2`.
- Teclado: `INPUT_KEYBOARD` + VK.

## Assinaturas

Mesma superfície pública reexportada por `core.sendinput` (ver `DOC_sendinput-py.md`).
