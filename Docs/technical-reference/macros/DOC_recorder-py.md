# DOC — macros/recorder.py

## Objetivo

Gravar eventos de mouse e teclado com timestamps relativos via listeners `pynput` e limpar as pontas da gravação.

## Dependências

- `pynput.mouse`, `pynput.keyboard` (import tardio em `start`)
- `hotkeys.keynames.describe_key`
- `core.keys` (`modifier_family`, `name_to_vk`)
- `core.sendinput.button_from_pynput`

## Lógica central

- `start()` zera a lista, marca `t0 = perf_counter`, sobe listeners daemon.
- Movimentos: throttle `_MOVE_MIN_INTERVAL_S` (16 ms) para limitar volume.
- Formato: `{"t": float, "kind": str, ...}` com kinds `mouse_move`, `mouse_down`, `mouse_up`, `mouse_scroll` (`x`, `y`, `dx`, `dy`), `key_down`, `key_up`.
- Eventos de tecla: `{"key": nome, "vk"?: código Win32, "char"?: caractere}` — código e caractere permitem reproduzir qualquer tecla.
- `set_ignore_point(predicate)`: cliques em pontos para os quais o predicado devolve `True` não são gravados (cliques no próprio Clickr).
- `stop(strip_tokens=None)` encerra os listeners, aplica `sanitize_events` e devolve cópia dos eventos.
- `sanitize_events(events, strip_tokens)`:
  - remove, do fim, os eventos de tecla cujas teclas pertencem ao atalho de gravação (movimentos de mouse intercalados são mantidos);
  - remove `key_up` / `mouse_up` sem o "down" anterior;
  - remove `key_down` sem "up" **apenas** das teclas do atalho (as demais ficam; o player as solta).
- `set_on_change(callback)` é chamado a cada evento e a cada mudança de estado.

## Assinaturas

| Símbolo | Retorno |
|---------|---------|
| `start() -> bool` | inicia gravação (False se já gravando) |
| `stop(strip_tokens=None) -> list[dict]` | eventos saneados |
| `get_events() / set_events(events) / clear()` | memória da macro |
| `is_recording() / event_count() / duration_ms()` | estado |
| `set_ignore_point(predicate)` / `set_on_change(callback)` | ganchos |
| `sanitize_events(events, strip_tokens=None)` (função) | lista limpa |
