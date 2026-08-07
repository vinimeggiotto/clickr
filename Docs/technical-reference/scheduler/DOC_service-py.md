# DOC — scheduler/service.py

## Objetivo

Agendar um único callback em `datetime` local (naive) usando `threading.Timer`.

## Dependências

- `datetime`, `threading`

## Lógica central

- `schedule(when, on_fire)` cancela timer anterior, valida futuro, agenda delay em segundos.
- `_fire()` limpa estado e chama `on_fire` uma vez; exceção → `last_error`.
- `cancel()` cancela timer e limpa `when`.

## Assinaturas

| Método | Papel |
|--------|--------|
| `schedule(when, on_fire)` | agenda |
| `cancel() -> bool` | cancela |
| `status() -> dict` | `active`, `at`, `last_error` |
| `is_active() / scheduled_at() / last_error()` | consulta |
