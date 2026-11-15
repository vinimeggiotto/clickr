# DOC — hotkeys/backend_pynput.py

## Objetivo

Detectar atalhos globais por um listener de teclado `pynput` — backend de macOS/Linux e reserva no Windows para combos que `RegisterHotKey` recusa.

## Dependências

- `pynput.keyboard` (import tardio em `start`)
- `core.keys` (`modifier_family`, `name_to_vk`)
- `hotkeys.keynames.describe_key`, `hotkeys.combo.Combo`

## Lógica central

- `key_vk(key, listener)`: converte a tecla pynput no VK canônico (usa o `vk` nativo no Windows; nos demais SOs resolve pelo nome). Se a tecla não for identificável, tenta `listener.canonical(key)` — com Ctrl/Alt pressionado o SO pode entregar um caractere de controle.
- Mantém o conjunto de famílias de modificador pressionadas e o conjunto de teclas principais pressionadas.
- No press de uma tecla não modificadora: se já estava pressionada, é auto-repetição e é ignorada; senão, dispara `on_action` para cada ação cujo combo tem aquele `vk` **e exatamente** os mesmos modificadores.
- **Não bloqueia** a tecla para os outros programas.
- `pause()` deixa de disparar; `resume()` limpa o estado de teclas antes de voltar.
- `apply` nunca recusa combos (devolve `{}`).
- `is_pressed(combo)`: a tecla principal está no conjunto de pressionadas.

## Assinaturas

| Símbolo | Entrada | Saída |
|---------|---------|--------|
| `key_vk(key, listener=None)` | tecla pynput | `int` ou `None` |
| `PynputHotkeyBackend(on_action)` | callback `(str) -> None` | instância |
| `start()` / `stop()` | — | ciclo do listener |
| `apply(bindings)` | `dict[str, Combo]` | `{}` |
| `pause()` / `resume()` | — | suspende / retoma |
| `is_pressed(combo)` | `Combo` | `bool` |
