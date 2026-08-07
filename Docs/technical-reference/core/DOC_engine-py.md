# DOC — core/engine.py

## Objetivo

Executar o loop de autoclique em thread dedicada, aplicando `ClickConfig` (intervalo, jitter, burst, sequência, filtro, botões L/R/M/X1/X2) e expondo `RuntimeState`.

## Dependências

- `core.sendinput` — emissão dos eventos de mouse
- `core.types.ClickConfig`, `RuntimeState`
- `window_filter.WindowFilter` — `allows()` antes de cada clique
- `sequence.SequenceRunner` — alvo XY + delay do passo
- `threading`, `time`, `random` (stdlib)

## Lógica central

- Antes do loop: espera `start_delay_ms` (interrompido por stop).
- Espera = `base ± jitter_ms` via `perf_counter` (base = interval ou delay do passo).
- Burst: N cliques com intervalo entre eles; depois só `burst_pause_ms`.
- `WindowFilter.allows()` falso → pula clique (não avança sequência).
- Sequência não vazia → posição do passo atual; avança após clique bem-sucedido.
- `hold`: `button_down` uma vez; depois só observa stop/duração; `button_up` no fim.
- `OSError` do SendInput grava `last_error` e encerra o loop.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `start()` | — | `bool` (False se já rodando) |
| `stop()` | — | `bool` |
| `toggle()` | — | `bool` (True se passou a rodar) |
| `update_config(data)` | `dict` parcial | `ClickConfig` |
| `get_config()` | — | `ClickConfig` |
| `get_state()` | — | `RuntimeState` |
| `set_last_error(message)` | `str \| None` | — |
| `is_running()` | — | `bool` |
