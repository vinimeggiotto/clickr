# DOC — app/single_instance.py

## Objetivo

Garantir um único Clickr em execução por usuário e permitir que uma segunda abertura peça à primeira que mostre a janela.

## Dependências

- `app.paths.user_data_dir`
- Windows: `kernel32.CreateMutexW` via `ctypes`
- macOS / Linux: `fcntl.flock`
- `threading`, `os`, `pathlib`

## Lógica central

- `acquire()`:
  - Windows: cria o mutex `Local\Clickr.SingleInstance.v1`; `ERROR_ALREADY_EXISTS` (183) → `False`.
  - macOS / Linux: abre `{dir}/clickr.lock` e tenta `LOCK_EX | LOCK_NB`; falha → `False`.
  - Qualquer impossibilidade de coordenar (diretório não criável, mutex/arquivo indisponível) → `True` (não bloqueia o app).
- `request_show()` (segunda instância): grava `{dir}/show.request` com o PID; erros de disco são ignorados.
- `watch(on_show, interval_s=0.5)` (instância principal): apaga pedido antigo, sobe a thread daemon `SingleInstanceWatch` que, a cada intervalo, detecta o arquivo, apaga-o e chama `on_show()`.
- `release()`: para a thread de observação e fecha o handle/arquivo.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `SingleInstance(directory=None)` | diretório opcional (padrão `user_data_dir()`) | instância |
| `acquire()` | — | `bool` (True = pode seguir) |
| `request_show()` | — | — |
| `watch(on_show, interval_s=0.5)` | callback | — |
| `release()` | — | — |
