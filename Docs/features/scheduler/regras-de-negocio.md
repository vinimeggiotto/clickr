# Feature: Scheduler (agendar início)

## Objetivo

Agendar um único disparo do motor de clique em data/hora **local**.

## Comportamento

1. Entrada: string ISO naive (`YYYY-MM-DDTHH:MM` ou com segundos), interpretada como horário local.
2. Horário deve ser **no futuro**; caso contrário, erro em `last_error` (sem disparo silencioso).
3. No disparo: para runners Tier 3 e chama `ClickEngine.start()`.
4. **Cancelar** remove o timer pendente.
5. Apenas um agendamento ativo por vez (novo `schedule_set` substitui o anterior).
6. Sem retry: se o callback falhar, o erro fica em `Scheduler.last_error` e aparece no estado.

## Bridge

| Método | Papel |
|--------|--------|
| `schedule_set(when)` | agenda |
| `schedule_cancel()` | cancela |

Estado em `get_state().schedule`: `active`, `at` (ISO ou null).

## UI

Aba **Agenda** com `datetime-local` (oculta no modo compacto).
