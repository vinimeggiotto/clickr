# DOC — scheduler/service.py

## Objetivo

Manter no máximo um agendamento ativo e disparar um callback em `datetime` local (naive), uma vez ou de forma recorrente.

## Dependências

- `datetime`, `threading` (stdlib)
- `core.errors` (`ClickrError`, `error_from_exception`)

## Lógica central

- `normalize_schedule(data)` valida `{at, repeat, interval_s, target, profile}`: `at` ISO/datetime sem timezone; `repeat` ∈ `REPEATS` (`once` / `daily` / `interval`); `target` ∈ `TARGETS` (`engine` / `macro` / `script` / `profile`); `interval_s` entre `MIN_INTERVAL_S` (5) e `MAX_INTERVAL_S` (7 dias) quando `repeat = interval`; `profile` obrigatório quando `target = profile`. Erros: `schedule.empty`, `schedule.invalid`, `schedule.badInterval`, `schedule.needProfile`.
- `schedule(when, **options)`: horário passado → `schedule.past`, exceto `daily`, que rola para a próxima ocorrência do horário.
- `restore(data)`: reativa um agendamento salvo; `once` vencido é descartado (retorna `False`); recorrentes avançam para a próxima ocorrência.
- **Sem `threading.Timer`:** uma thread (`Scheduler`) confere o relógio de parede a cada segundo (ou antes, quando falta menos). O disparo permanece correto após suspender/retomar o computador ou ajustar o relógio.
- No disparo: `daily` avança um dia, `interval` avança `interval_s` a partir de agora, `once` é removido; depois chama `on_fire(item)` com `at` em ISO. Exceção do callback → `last_error` (sem retry).
- `cancel()` remove o agendamento; `shutdown()` encerra a thread **sem** apagar o agendamento (o controller o mantém em `settings.json`).
- `now` é injetável no construtor (testes).

## Assinaturas

| Método | Papel |
|--------|--------|
| `Scheduler(now=datetime.now)` | instância |
| `schedule(when, on_fire=None, **options)` | agenda; devolve a forma serializável |
| `restore(data) -> bool` | reativa agendamento salvo |
| `cancel() -> bool` | cancela |
| `shutdown()` | encerra a thread |
| `to_dict() -> dict \| None` | agendamento ativo serializável (`at` ISO) |
| `status() -> dict` | `active`, `at`, `repeat`, `interval_s`, `target`, `profile`, `last_error` |
| `is_active() / scheduled_at() / last_error() / clear_error()` | consulta |
| `set_on_fire(callback)` / `set_on_change(callback)` | ganchos |
| `normalize_schedule(data)` (função) | dict validado (ou `ClickrError`) |
