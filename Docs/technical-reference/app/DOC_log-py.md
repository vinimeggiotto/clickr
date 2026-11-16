# DOC — app/log.py

## Objetivo

Fornecer o logger do aplicativo, gravando em arquivo rotativo em `{user_data_dir()}/clickr.log`.

## Dependências

- `logging`, `logging.handlers.RotatingFileHandler` (stdlib)
- `app.paths.user_data_dir` (import tardio)

## Lógica central

- Logger nomeado `clickr`, nível `INFO`, sem propagação para o logger raiz.
- `setup_logging()` configura uma única vez: arquivo de até 512 KiB com 2 backups, UTF-8, formato `data nível [thread] mensagem`.
- Se o diretório ou o arquivo não puderem ser criados, usa `NullHandler` — falha de disco não derruba o app.
- `get_logger()` devolve o mesmo logger; módulos o obtêm na importação e passam a gravar depois que `main.py` chama `setup_logging()`.

## Assinaturas

| Função | Entrada | Saída |
|--------|---------|--------|
| `setup_logging()` | — | `logging.Logger` configurado |
| `get_logger()` | — | `logging.Logger` |

## Diagnóstico de partida

- `setup_logging()` também anexa o logger `pywebview` ao mesmo arquivo e grava uma linha inicial com as versões (Clickr, Python, pywebview, pynput, pystray, pythonnet) e o sistema operacional.
- `arm_startup_watchdog(seconds=20)` (chamado em `main.py`) usa `faulthandler.dump_traceback_later`: se a interface não carregar no prazo, a pilha de todas as threads é gravada em `clickr.log`. Não encerra o processo.
- `disarm_startup_watchdog()` cancela o despejo; é chamado na primeira execução de `AppController.get_settings`, que é a primeira chamada feita pela página ao carregar.
- `watchdog_armed()` informa se o watchdog está ativo.
