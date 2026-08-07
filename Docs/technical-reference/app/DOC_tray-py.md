# DOC — app/tray.py

## Objetivo

Expor ícone na bandeja do Windows com menu Mostrar / Ocultar / Sair (rótulos via catálogo i18n).

## Dependências

- `pystray`
- `PIL.Image` (Pillow)
- Asset obrigatório: `assets/icon.png` (marca Clickr)
- `scripts/generate_icon.py` gera PNG + ICO multi-tamanho (16–256); `build_exe.ps1` regenera antes do PyInstaller (`Clickr.spec` → `icon='assets\\icon.ico'`)
- Catálogos `ui/locales/{code}.json` (seção `tray.*`) via `app.paths.locales_dir`

## Lógica central

- `start()` carrega o PNG, cria `pystray.Icon` e roda `icon.run` em thread daemon.
- Rótulos vêm de `tray.show` / `hide` / `quit` / `notifyTitle` / `notifyBody`; chave ausente cai no catálogo `pt-BR`.
- `set_locale(code)` reconstrói o menu e chama `icon.update_menu()`.
- `notify_still_running()` usa título/corpo traduzidos do locale ativo.
- Itens do menu delegam aos callbacks injetados pelo `AppController`.
- Ausência do arquivo de ícone levanta `FileNotFoundError` (sem gerar ícone alternativo).

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `SystemTray(on_show, on_hide, on_quit, locale=None)` | callables + locale opcional | instância |
| `start()` | — | inicia thread da bandeja |
| `stop()` | — | encerra o ícone |
| `set_locale(code)` | BCP-47 | atualiza menu |
| `notify(message, title="Clickr")` | strings | toast/balloon do Windows |
| `notify_still_running()` | — | toast padrão traduzido |
