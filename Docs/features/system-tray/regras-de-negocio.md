# Feature: System tray e always-on-top

## Objetivo

Manter o Clickr acessível em segundo plano, controlável pela bandeja, e opcionalmente acima de outras janelas.

## Bandeja (pystray)

| Item | Ação |
|------|------|
| Iniciar / Parar | Rótulo fixo; o estado aparece no ícone (ponto verde). Parado: inicia o motor com a configuração atual. Com algo em execução (motor, macro, script ou gravação): para tudo |
| Mostrar (padrão) | Exibe e restaura a janela principal |
| Ocultar | Oculta a janela principal |
| Sair | Encerra motor, hotkeys, tray e destrói a janela |

- Ícone: `assets/icon.png` (visual alinhado ao `clickr_icon.svg`, regenerável via `scripts/generate_icon.py`). Se o arquivo faltar ou estiver corrompido, um ícone substituto é desenhado — a bandeja não deixa de abrir por isso.
- **Ícone ativo:** enquanto motor, macro ou script estão em execução, o ícone ganha um ponto verde no canto.
- Rótulos do menu e do toast seguem o `locale` em `settings.json` (catálogo `ui/locales/*.json`, chaves `tray.*`); ao trocar idioma na UI, o menu é atualizado.
- Fechar o × da janela **oculta** para a bandeja; encerramento real só via **Sair** (rótulo traduzido).
- Ao pedir para fechar (×): modal na UI explica que o app segue na bandeja; ao confirmar, a janela some.
- O toast/balloon “continua na bandeja” (`pystray.Icon.notify`) aparece **só na primeira vez** (`tray_hint_shown` em `settings.json`).
- “Ocultar” no menu da bandeja não exige o modal (já está na bandeja).
- Se a bandeja não puder ser criada, o erro é registrado no log e o app segue: nesse caso fechar a janela **encerra** o programa.
- No macOS o ícone é iniciado na thread principal (`run_detached`) antes do loop do pywebview.

## Always on top

- Preferência do aplicativo `always_on_top` (default `true`) em `settings.json` — não faz mais parte de `ClickConfig`.
- Aplicado via API da janela pywebview (`window.on_top`) no boot e a cada mudança.
- Toggle na aba Run (`set_preferences({ always_on_top })` / `set_always_on_top`).
- Perfis v2 não alteram essa opção; perfis da 1.0.x que trazem `always_on_top` continuam aplicando o valor ao serem carregados.

## Regras

- A posição da janela é lembrada entre sessões (`window_pos`).
- Iniciado com `--minimized`, o app abre só na bandeja; sem bandeja disponível, a janela é mostrada.
