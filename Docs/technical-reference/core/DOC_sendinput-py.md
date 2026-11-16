# DOC — core/sendinput.py

## Objetivo

Fachada de input multiplataforma com API pública estável para mouse (incl. X1/X2 quando disponível, rolagem) e teclado (por VK, por nome, por caractere e digitação de texto).

## Dependências

- Variável de ambiente `CLICKR_INPUT_BACKEND` e `sys.platform` para escolher o backend
- Windows: `core.sendinput_win32` (ctypes / `user32` SendInput)
- macOS / Linux: `core.sendinput_pynput` (pynput)
- Testes / sem display: `core.sendinput_null`
- Tabela de teclas compartilhada: `core.keys`

## Lógica central

- Seleção do backend na importação: `CLICKR_INPUT_BACKEND=null` (sem diferenciar maiúsculas) → backend nulo; senão `win32` no Windows; senão pynput.
- Reexporta as mesmas funções em todos os backends.
- Windows: coordenadas de ponto fixo usam tela virtual (`SM_*VIRTUALSCREEN`) normalizadas para SendInput **0–65535**, com `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK`.
- macOS: tela virtual via Quartz (`CGGetActiveDisplayList` / `CGDisplayBounds`).
- Linux: métricas via Xlib (`XDisplayWidth` / `XDisplayHeight`); exige sessão X11.
- Botões `x1`/`x2`: plenos no Win32; no pynput só se o enum `Button` expuser `x1`/`x2` — senão `OSError` explícito.
- `click_at` / `double_click_at` aceitam `restore=True` para devolver o cursor à posição original.
- Teclado: API por VK (`key_down`/`key_up`/`key_press`), por nome (`key_*_name`, via `core.keys.name_to_vk`), por caractere (`key_down_char`/`key_up_char`) e `type_text`.
- Falhas de envio/consulta levantam `OSError` (sem retry).

## Assinaturas

| Função | Entrada | Saída / efeito |
|--------|---------|----------------|
| `get_cursor_pos()` | — | `(x, y)` pixels |
| `get_virtual_screen_rect()` | — | `(x, y, width, height)` |
| `move_absolute(x, y)` | pixels | move cursor |
| `click(button)` | `left\|right\|middle\|x1\|x2` | clique no cursor |
| `click_at(button, x, y, restore=False, count=1)` | botão + XY | move + `count` cliques (+ volta do cursor) |
| `double_click(button)` | botão | dois cliques no cursor |
| `double_click_at(button, x, y, restore=False)` | botão + XY | dois cliques no ponto |
| `button_down(button)` / `button_up(button)` | botão | pressionar / soltar |
| `scroll(dy, dx=0)` | "cliques" de roda | `dy > 0` para cima, `dx > 0` para a direita |
| `name_to_vk(name)` | nome tecla | VK int |
| `key_down` / `key_up` / `key_press` | VK | teclado |
| `key_*_name(name)` | nome | teclado por nome |
| `key_down_char(char)` / `key_up_char(char)` | caractere | tecla por caractere (independe da tabela de nomes) |
| `type_text(text)` | string | digita o texto |
| `button_from_pynput(button)` | botão pynput | `ButtonName` ou `None` |
