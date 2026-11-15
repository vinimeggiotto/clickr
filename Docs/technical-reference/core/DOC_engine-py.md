# DOC — core/engine.py

## Objetivo

Executar o loop de autoclique (mouse ou teclado) em thread dedicada, aplicando `ClickConfig` (intervalo, jitter, burst, sequência, filtro, guards) e expondo `RuntimeState`.

## Dependências

- `core.sendinput` — emissão dos eventos de mouse e teclado
- `core.keys.parse_key_sequence` — tecla/combinação da ação de teclado
- `core.types.ClickConfig`, `RuntimeState`
- `window_filter.WindowFilter` — `allows()` antes de cada ação
- `sequence.SequenceRunner` — alvo XY + delay do passo
- `threading`, `time`, `random`, `collections.deque` (stdlib); `winmm` via `ctypes` no Windows

## Lógica central

- **Fases:** `idle` → `countdown` (se `start_delay_ms > 0`; `starts_at` = epoch do fim do delay) → `running`. `elapsed_ms` conta a partir do fim do delay e é congelado ao parar.
- **Esperas por deadline:** cada espera mira um instante agendado (`anchor + intervalo`), de modo que o tempo da ação não se soma ao intervalo. Atraso acima de `_RESYNC_LATE_S` (20 ms) ressincroniza a partir de agora. Os últimos `_SPIN_S` (1,5 ms) são feitos em espera ativa; o restante em `Event.wait` (interrompível por stop).
- `_TimerResolution`: no Windows chama `timeBeginPeriod(1)` / `timeEndPeriod(1)` em volta do loop.
- Espera = `base ± jitter_ms` (base = interval ou delay do passo). Burst: N ações com intervalo entre elas; depois só `burst_pause_ms`.
- **Ação pulada** (retorna 0, não avança a sequência, grava `blocked`):
  - `WindowFilter.allows()` falso → `"filter"`;
  - mouse: `click_guard(x, y)` verdadeiro (no modo cursor usa a posição atual do ponteiro) → `"own_window"`;
  - teclado: `key_guard()` verdadeiro → `"own_window"`.
  Exceção dentro de um guard é tratada como "não bloqueia".
- **Mouse:** alvo = passo da sequência (exceto em hold), ou ponto fixo, ou cursor. `position_jitter_px` soma deslocamento uniforme por eixo a pontos fixos/da sequência. `restore_cursor` é repassado a `click_at` / `double_click_at`.
- **Teclado** (`action == "key"`): pressiona os VKs de `key_name` em ordem e solta em ordem inversa; duplo repete duas vezes; hold pressiona uma vez e mantém.
- `hold`: `button_down` (ou teclas) uma vez; depois só observa stop/duração em passos de 50 ms; libera tudo no fim.
- `actual_cps`: soma das ações registradas no último segundo (`deque` de carimbos).
- `OSError` / `ValueError` da ação gravam `last_error` e encerram o loop.
- `on_tick` é chamado a cada mudança de estado e sempre ao final (limite, erro ou stop); deve apenas sinalizar.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `start()` | — | `bool` (False se já rodando) |
| `stop()` | — | `bool` |
| `toggle()` | — | `bool` (True se passou a rodar) |
| `update_config(data)` | `dict` parcial (chaves desconhecidas ignoradas) | `ClickConfig` |
| `get_config()` | — | `ClickConfig` (cópia) |
| `get_state()` | — | `RuntimeState` |
| `set_last_error(message)` | objeto ou `None` | — |
| `is_running()` | — | `bool` |
| `set_on_tick(callback)` | `() -> None` ou `None` | — |
| `set_click_guard(guard)` | `(x, y) -> bool` ou `None` | — |
| `set_key_guard(guard)` | `() -> bool` ou `None` | — |
| `window_filter` | — | `WindowFilter` (propriedade) |
