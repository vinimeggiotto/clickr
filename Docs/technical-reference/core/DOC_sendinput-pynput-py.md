# DOC — core/sendinput_pynput.py

## Objetivo

Implementar a API de input em macOS e Linux usando `pynput` (já em `requirements.txt`).

## Dependências

- `pynput.mouse` / `pynput.keyboard`
- macOS: Quartz via `ctypes` (tela virtual)
- Linux: libX11 via `ctypes` (tela; exige X11)

## Lógica central

- Mouse: `Controller.position`, `press`/`release`/`click`.
- `x1`/`x2`: só se `Button.x1` / `Button.x2` existirem; caso contrário `OSError`.
- Teclado: mapeia VK (mesma tabela Windows) para `Key` / `KeyCode` pynput.
- Linux sem libX11 ou sem display: `OSError` explícito (Wayland não é caminho alternativo silencioso).

## Assinaturas

Mesma superfície pública reexportada por `core.sendinput` (ver `DOC_sendinput-py.md`).
