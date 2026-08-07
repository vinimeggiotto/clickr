# Feature: Macro (gravar / reproduzir)

## Objetivo

Capturar sequência de eventos de mouse e teclado com timestamps e reproduzi-la via SendInput.

## Comportamento

1. **Gravar** inicia listeners `pynput` (mouse + teclado). Eventos: `mouse_move` (throttle ~16 ms), `mouse_down`/`mouse_up`, `key_down`/`key_up`.
2. Timestamps são relativos ao início da gravação (`perf_counter`).
3. **Parar gravação** fecha os listeners e mantém a lista em memória.
4. **Reproduzir** despacha cada evento pelo caminho SendInput (`core.sendinput`), respeitando delays relativos.
5. Hotkey global **não** alterna o motor durante gravação; durante reprodução a hotkey **para** a macro.
6. Motor de autoclique e script são parados ao gravar/reproduzir (exclusão mútua no controller).
7. **Limpar** só é permitido com macro parada.

## Bridge

| Método | Papel |
|--------|--------|
| `macro_record_start` / `macro_record_stop` | gravação |
| `macro_play` / `macro_stop` | reprodução |
| `macro_clear` | limpa eventos |

Estado em `get_state().macro`: `recording`, `playing`, `event_count`.

## UI

Aba **Macro** (oculta no modo compacto).
