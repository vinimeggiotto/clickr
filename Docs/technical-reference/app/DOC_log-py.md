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
