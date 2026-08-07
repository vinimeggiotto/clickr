# DOC — macros/recorder.py

## Objetivo

Gravar eventos de mouse e teclado com timestamps relativos via listeners `pynput`.

## Dependências

- `pynput.mouse`, `pynput.keyboard`
- `hotkeys.service.format_key`
- `core.sendinput.button_from_pynput`

## Lógica central

- `start()` zera a lista, marca `t0 = perf_counter`, sobe listeners daemon.
- Movimentos: throttle `_MOVE_MIN_INTERVAL_S` (16 ms) para limitar volume.
- `stop()` encerra listeners e devolve cópia dos eventos.
- Formato: `{"t": float, "kind": str, ...}` com kinds `mouse_move`, `mouse_down`, `mouse_up`, `key_down`, `key_up`.

## Assinaturas

| Método | Retorno |
|--------|---------|
| `start() -> bool` | inicia gravação |
| `stop() -> list[dict]` | eventos |
| `get_events() / set_events / clear` | memória da macro |
| `is_recording() / event_count()` | estado |
