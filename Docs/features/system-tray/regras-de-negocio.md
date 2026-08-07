# Feature: System tray e always-on-top

## Objetivo

Manter o Clickr acessível em segundo plano e opcionalmente acima de outras janelas.

## Bandeja (pystray)

| Item | Ação |
|------|------|
| Mostrar | Exibe a janela principal |
| Ocultar | Oculta a janela principal |
| Sair | Encerra motor, hotkeys, tray e destrói a janela |

- Ícone: `assets/icon.png` (obrigatório; visual alinhado ao `clickr_icon.svg`, regenerável via `scripts/generate_icon.py`).
- Rótulos do menu e do toast seguem o `locale` em `settings.json` (catálogo `ui/locales/*.json`, chaves `tray.*`); ao trocar idioma na UI, o menu é atualizado.
- Fechar o × da janela **oculta** para a bandeja; encerramento real só via **Sair** (rótulo traduzido).
- Ao pedir para fechar (×): modal na UI explica que o app segue na bandeja; ao confirmar, a janela some e o Windows recebe um toast/balloon via `pystray.Icon.notify` (textos traduzidos).
- “Ocultar” no menu da bandeja não exige o modal (já está na bandeja).

## Always on top

- Campo `always_on_top` (default `true`).
- Aplicado via API da janela pywebview (`window.on_top`).
- Toggle na aba Run; também restaurado ao carregar perfil.
