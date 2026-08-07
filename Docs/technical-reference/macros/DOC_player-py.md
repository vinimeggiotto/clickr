# DOC — macros/player.py

## Objetivo

Reproduzir lista de eventos de macro usando `core.sendinput` (mesmo caminho do motor).

## Dependências

- `core.sendinput` (move, button_down/up, key_down/up por nome)
- `threading`, `time.perf_counter`

## Lógica central

- Thread `MacroPlayer`: para cada evento, espera até `t` relativo desde o início da reprodução; depois despacha.
- `stop()` seta evento e faz join curto (2 s).
- Erros de despacho vão para `last_error`; `on_done` / `on_tick` notificam a UI.

## Assinaturas

| Método | Papel |
|--------|--------|
| `play(events) -> bool` | inicia se não estiver tocando e lista não vazia |
| `stop() -> bool` | interrompe |
| `is_playing() / last_error()` | estado |
