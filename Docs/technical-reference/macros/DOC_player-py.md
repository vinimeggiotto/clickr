# DOC — macros/player.py

## Objetivo

Reproduzir lista de eventos de macro usando `core.sendinput` (mesmo caminho do motor), com repetição e fator de velocidade.

## Dependências

- `core.sendinput` (move, button_down/up, scroll, key_down/up por VK, key_down/up por caractere)
- `core.keys.name_to_vk`, `core.errors`
- `threading`, `time.perf_counter`

## Lógica central

- Thread `MacroPlayer`: executa a lista `repeat` vezes; em cada rodada espera até `t / speed` desde o início da rodada e despacha o evento.
- `repeat` é limitado a ≥ 1; `speed` inválido ou ≤ 0 vira `1.0`.
- Despacho: `mouse_move` → move; `mouse_down`/`mouse_up` → move + botão; `mouse_scroll` → move + rolagem; `key_down`/`key_up` → tecla. Kind desconhecido → `macro.unknownEvent`.
- Resolução da tecla: `vk` gravado (somente no Windows) → nome (`name_to_vk`) → `char`; nenhum → `macro.unsupportedKey`. Eventos antigos (só `key`) continuam válidos.
- **Pressionados:** toda tecla/botão em "down" é registrada; `_release_all` solta o que restar entre repetições e ao terminar/interromper.
- `play` com lista vazia grava `macro.empty` em `last_error` e devolve `False`.
- `stop()` seta evento e faz join curto (2 s).
- Erros de despacho vão para `last_error` (dict de erro); `on_done` / `on_tick` notificam a UI.

## Assinaturas

| Método | Papel |
|--------|--------|
| `play(events, repeat=1, speed=1.0) -> bool` | inicia se não estiver tocando e lista não vazia |
| `stop() -> bool` | interrompe |
| `is_playing()` | estado |
| `progress() -> dict` | `iteration`, `repeat` |
| `last_error()` / `clear_error()` | dict de erro ou `None` |
| `set_on_done(callback)` / `set_on_tick(callback)` | ganchos |
