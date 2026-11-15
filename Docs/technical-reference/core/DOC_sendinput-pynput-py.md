# DOC — core/sendinput_pynput.py

## Objetivo

Implementar a API de input em macOS e Linux usando `pynput` (já em `requirements.txt`).

## Dependências

- `pynput.mouse` / `pynput.keyboard`
- `core.keys.name_to_vk` (tabela de teclas compartilhada)
- macOS: Quartz via `ctypes` (tela virtual)
- Linux: libX11 via `ctypes` (tela; exige X11)

## Lógica central

- Mouse: `Controller.position`, `press`/`release`/`click`, `scroll(dx, dy)`.
- `click_at(..., restore=True)` guarda a posição antes de mover e a repõe depois dos cliques; `count` define o número de cliques.
- `x1`/`x2`: só se `Button.x1` / `Button.x2` existirem; caso contrário `OSError`.
- Teclado: `_VK_TO_KEY` mapeia VK (numeração Windows) para `Key` / `KeyCode` pynput — teclas nomeadas, F1–F24, letras, dígitos, pontuação OEM do layout US, teclado numérico e variantes esquerda/direita dos modificadores (cada uma cai no primeiro membro existente do enum). VK sem mapeamento → `OSError`.
- `key_down_char` / `key_up_char` usam `KeyCode.from_char`; `type_text` usa `Controller.type`.
- Linux sem libX11 ou sem display: `OSError` explícito (Wayland não é caminho alternativo silencioso).

## Assinaturas

Mesma superfície pública reexportada por `core.sendinput` (ver `DOC_sendinput-py.md`).
