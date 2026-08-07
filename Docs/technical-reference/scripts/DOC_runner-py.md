# DOC — scripts/runner.py

## Objetivo

Parsear e executar DSL mínima (`click`, `move`, `wait`, `key`, `loop`/`end`) via SendInput.

## Dependências

- `core.sendinput` (click, move_absolute, key_press_name, name_to_vk)

## Lógica central

- `parse_script(source)` → lista de `Command` (dataclasses); valida limites de linhas/loop/profundidade.
- `ScriptRunner.run(source)` parseia, sobe thread e executa; `wait` usa `perf_counter` + sleep curto interruptível.
- `stop()` seta evento e join.

## Assinaturas

| Símbolo | Papel |
|---------|--------|
| `parse_script(source) -> list[Command]` | parser |
| `ScriptRunner.run(source) -> bool` | executa |
| `ScriptRunner.stop() -> bool` | para |
| `ScriptRunner.status() -> dict` | `running`, `line`, `last_error` |
