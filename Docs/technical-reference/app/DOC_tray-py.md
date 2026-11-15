# DOC — app/tray.py

## Objetivo

Expor ícone na bandeja (Windows / macOS / Linux via pystray) com menu Iniciar/Parar, Mostrar, Ocultar e Sair (rótulos via catálogo i18n) e indicação visual de execução.

## Dependências

- `pystray`
- `PIL.Image` / `PIL.ImageDraw` (Pillow)
- Asset `assets/icon.png` (marca Clickr)
- `scripts/generate_icon.py` gera PNG + ICO; scripts de build regeneram antes do PyInstaller (`packaging/Clickr.*.spec`)
- Catálogos `ui/locales/{code}.json` (seção `tray.*`) via `app.paths.locales_dir`

## Lógica central

- `start(detached=False)` carrega o ícone, gera a variante "ativa" (ponto verde no canto) e cria `pystray.Icon`. No macOS, ou com `detached=True`, usa `run_detached()` (thread principal); nos demais SOs roda `icon.run` em thread daemon.
- Ícone ausente ou corrompido não impede a bandeja: um ícone substituto é desenhado.
- Menu: se `on_toggle` foi informado, o primeiro item é Iniciar/Parar com rótulo dinâmico (`tray.start` / `tray.stop` conforme `set_running`), seguido de separador; depois Mostrar (item padrão), Ocultar, separador e Sair.
- Rótulos vêm de `tray.show` / `hide` / `quit` / `start` / `stop` / `notifyTitle` / `notifyBody`; chave ausente cai no catálogo `pt-BR`.
- `set_running(running)` troca o ícone (normal/ativo) e atualiza o menu.
- `set_locale(code)` reconstrói o menu e chama `icon.update_menu()`.
- `notify_still_running()` usa título/corpo traduzidos do locale ativo; `notify` não faz nada se o backend não suporta notificação (`HAS_NOTIFICATION`).
- Itens do menu delegam aos callbacks injetados pelo `AppController`.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `SystemTray(on_show, on_hide, on_quit, on_toggle=None, locale=None)` | callables + locale opcional | instância |
| `start(detached=False)` | bool | inicia o ícone |
| `stop()` | — | encerra o ícone |
| `set_locale(code)` | BCP-47 | atualiza menu; `ValueError` se inválido |
| `set_running(running)` | bool | ícone ativo + rótulo Iniciar/Parar |
| `notify(message, title="Clickr")` | strings | toast/balloon |
| `notify_still_running()` | — | toast padrão traduzido |
