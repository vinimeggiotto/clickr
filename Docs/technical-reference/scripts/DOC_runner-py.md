# DOC — scripts/runner.py

## Objetivo

Parsear e executar a DSL de script (`click`, `dclick`, `move`, `drag`, `scroll`, `wait`, `key`, `type`, `loop`/`end`) pela fachada de input.

## Dependências

- `core.sendinput` (click, double_click, click_at, move_absolute, button_down/up, scroll, key_down/up, type_text)
- `core.keys.parse_key_sequence`
- `core.errors` (`ClickrError`, `error_from_exception`)

## Lógica central

- `parse_script(source)` → lista de `Command` (dataclasses `CmdClick`, `CmdMove`, `CmdWait`, `CmdKey`, `CmdType`, `CmdScroll`, `CmdDrag`, `CmdLoop`), cada um com o **número da linha** de origem.
- Limites: `MAX_LINES = 500`, `MAX_LOOP_COUNT = 1000`, `MAX_LOOP_DEPTH = 2`, `MAX_TYPE_LEN = 2000`.
- Erros de parse são `ClickrError` com código `script.*` e parâmetros (`line`, `value`, `op`, `usage`, `max`): `empty`, `tooLong`, `unknownCommand`, `usage`, `badNumber`, `badButton`, `badKey`, `negativeWait`, `loopRange`, `loopDepth`, `endWithoutLoop`, `loopNoEnd`.
- `wait MIN-MAX` vira `CmdWait(ms, max_ms)` e sorteia a espera a cada execução; `key` guarda os VKs já resolvidos; `type` aceita aspas e escapes `\n`, `\t`, `\"`, `\'`.
- `ScriptRunner.run(source)` parseia, sobe thread e executa; erro de parse ou script sem comandos → `last_error` e retorna `False`.
- Execução: `key` pressiona os VKs em ordem e solta em ordem inversa; `drag` move ao início, pressiona, percorre `_DRAG_STEPS` (12) pontos intermediários em ~180 ms e solta; `wait` usa `perf_counter` + sleep curto interruptível.
- Erro em execução vira `last_error` com `params.line` da linha corrente.
- No fim (normal, erro ou stop), `_release_held` solta botão e teclas que ficaram pressionados.
- `stop()` seta evento e join (2 s).

## Assinaturas

| Símbolo | Papel |
|---------|--------|
| `parse_script(source) -> list[Command]` | parser |
| `parse_combo(text) -> tuple[int, ...]` | VKs de `'CTRL+SHIFT+A'` |
| `ScriptRunner.run(source) -> bool` | executa |
| `ScriptRunner.stop() -> bool` | para |
| `ScriptRunner.status() -> dict` | `running`, `line`, `last_error` |
| `ScriptRunner.is_running() / current_line() / last_error() / clear_error()` | consulta |
| `ScriptRunner.set_on_done(callback)` / `set_on_tick(callback)` | ganchos |
