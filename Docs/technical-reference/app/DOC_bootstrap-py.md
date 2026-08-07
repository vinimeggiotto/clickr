# DOC — app/bootstrap.py

## Objetivo

Criar a janela pywebview do Clickr e amarrar o ciclo de vida (start, closing→tray, closed→shutdown).

## Dependências

- `webview`
- `app.controller.AppController`

## Lógica central

- Janela 468×676, `frameless=True`, `easy_drag=False`, `on_top=True` inicial, `js_api=controller` (title bar HTML + rail lateral).
- `events.closing`: se não houver quit explícito, oculta a janela e cancela o close (`return False`).
- `events.closed`: chama `controller.shutdown()`.
- `webview.start(on_start)` inicia hotkeys/tray após a GUI subir.

## Assinaturas

| Função | Entrada | Saída |
|--------|---------|--------|
| `create_app()` | — | `(Window, AppController)` |
| `run()` | — | inicia loop GUI (bloqueante) |
