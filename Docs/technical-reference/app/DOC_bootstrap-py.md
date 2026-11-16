# DOC — app/bootstrap.py

## Objetivo

Criar a janela pywebview do Clickr, garantir instância única e amarrar o ciclo de vida (start, closing→tray, closed→shutdown) em qualquer SO suportado.

## Dependências

- `webview`
- `app.controller.AppController`
- `app.single_instance.SingleInstance`
- `app.paths.ui_dir`, `app.log`

## Lógica central

- Sem bloqueio por plataforma (Windows / macOS / Linux).
- `run()` começa por `SingleInstance.acquire()`: se já houver um Clickr aberto, chama `request_show()` e retorna sem criar janela. Na instância principal, `watch(controller.show_window)` atende esses pedidos; a trava é liberada no `finally`.
- Janela 468×676, `frameless=True`, `easy_drag=False`, `on_top=True` inicial, `js_api=controller` (title bar HTML + rail lateral); posição inicial = `controller.initial_window_pos()` quando houver.
- `start_minimized=True` cria a janela com `hidden=True` e avisa o controller (`mark_window_hidden`).
- `webview.start(on_start)`: após a GUI subir chama `controller.bootstrap_services()` (falha é registrada no log). Se iniciou minimizado e não há bandeja, mostra a janela.
- `events.closing`: se `controller.should_close_to_tray()` (há bandeja e não houve quit explícito), oculta a janela e cancela o close (`return False`); senão deixa fechar.
- `events.closed`: chama `controller.shutdown()`.
- macOS: `controller.start_tray(detached=True)` é chamado na thread principal antes de `webview.start` (exigência do pystray).

## Assinaturas

| Função | Entrada | Saída |
|--------|---------|--------|
| `create_app(start_minimized=False)` | bool | `(Window, AppController)` |
| `run(start_minimized=False)` | bool | inicia loop GUI (bloqueante) |

## "Sempre no topo" na criação

`create_app` passa `on_top=controller.initial_on_top()` a `webview.create_window`. Nada altera a janela nativa durante a partida: no WinForms, mudar `TopMost` a partir de outra thread enquanto o WebView2 inicializa trava a interface.
