# DOC — core/sendinput.py

## Objetivo

Fachada de input multiplataforma com API pública estável para mouse (incl. X1/X2 quando disponível) e teclado.

## Dependências

- `sys.platform` para escolher o backend
- Windows: `core.sendinput_win32` (ctypes / `user32` SendInput)
- macOS / Linux: `core.sendinput_pynput` (pynput)

## Lógica central

- Reexporta as mesmas funções em todos os SOs.
- Windows: coordenadas de ponto fixo usam tela virtual (`SM_*VIRTUALSCREEN`) normalizadas para SendInput **0–65535**, com `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK`.
- macOS: tela virtual via Quartz (`CGGetActiveDisplayList` / `CGDisplayBounds`).
- Linux: métricas via Xlib (`XDisplayWidth` / `XDisplayHeight`); exige sessão X11.
- Botões `x1`/`x2`: plenos no Win32; no pynput só se o enum `Button` expuser `x1`/`x2` — senão `OSError` explícito.
- Teclado: API por VK (`name_to_vk`, `key_down`/`key_up`/`key_press`) e por nome (`key_*_name`).
- Falhas de envio/consulta levantam `OSError` (sem retry).

## Assinaturas

| Função | Entrada | Saída / efeito |
|--------|---------|----------------|
| `get_cursor_pos()` | — | `(x, y)` pixels |
| `get_virtual_screen_rect()` | — | `(x, y, width, height)` |
| `move_absolute(x, y)` | pixels | move cursor |
| `click(button)` | `left\|right\|middle\|x1\|x2` | clique no cursor |
| `click_at(button, x, y)` | botão + XY | move + clique |
| `double_click(button)` | botão | dois cliques no cursor |
| `double_click_at(button, x, y)` | botão + XY | dois cliques no ponto |
| `button_down(button)` / `button_up(button)` | botão | pressionar / soltar |
| `name_to_vk(name)` | nome tecla | VK int |
| `key_down` / `key_up` / `key_press` | VK | teclado |
| `key_*_name(name)` | nome | teclado por nome |
| `button_from_pynput(button)` | botão pynput | `ButtonName` ou `None` |
