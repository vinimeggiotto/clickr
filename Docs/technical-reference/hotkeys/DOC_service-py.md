# DOC — hotkeys/service.py

## Objetivo

Manter um atalho global (combinação) por ação, despachar a ação quando o atalho é pressionado e capturar a próxima combinação digitada pelo usuário.

## Dependências

- `hotkeys.combo` (`Combo`, `parse_combo`, `make_combo`)
- `hotkeys.backend_win32` (Windows) / `hotkeys.backend_pynput` (demais SOs e reserva)
- `hotkeys.keynames` (`describe_key`, `format_key` — reexportados)
- `core.keys.modifier_family`, `core.errors.ClickrError`, `app.log`
- `pynput.keyboard` (import tardio, só na captura)

## Lógica central

- Ações: `ACTIONS = ("toggle", "stop_all", "pick_point", "macro_record")`; padrão `toggle = F6`.
- `load_bindings(mapping)` nunca falha: combos inválidos ou repetidos são descartados e o de `toggle` volta a `F6`.
- `set_binding(action, text)` valida e aplica: ação desconhecida → `hotkey.unknownAction`; texto inválido → `hotkey.unsupported`; combo já usado por outra ação → `hotkey.conflict`. Texto vazio remove o atalho.
- Backend: no Windows tenta `Win32HotkeyBackend` (`RegisterHotKey`); se a criação falhar, usa `PynputHotkeyBackend`. Nos demais SOs, sempre pynput.
- **Despacho fora do hook:** o backend só enfileira; a thread `HotkeyDispatch` chama `on_action(ação)`, de modo que trabalho demorado não trava o input do sistema.
- `is_pressed(action)`: consulta ao backend se a tecla principal do combo está pressionada (base do modo "segurar").
- **Captura (`begin_capture`)**: pausa o backend, sobe um listener pynput temporário, acumula as famílias de modificador pressionadas e, na primeira tecla não modificadora, entrega o texto do combo. `ESC` sem modificadores entrega texto vazio (cancelado). Ao terminar/cancelar, o backend é retomado. O callback é entregue pela thread de despacho.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `HotkeyService(on_action, bindings=None)` | callback `(str) -> None`, mapa ação → texto | instância |
| `start()` / `stop()` | — | ciclo de vida do backend e do despacho |
| `load_bindings(mapping)` | mapa ação → texto | mapa efetivo |
| `bindings()` | — | `dict[str, str]` (vazio = sem atalho) |
| `combo(action)` | ação | `Combo` ou `None` |
| `set_binding(action, text)` | ação + texto | nome canônico (ou `ClickrError`) |
| `is_pressed(action)` | ação | `bool` |
| `begin_capture(on_captured)` | callback `(str) -> None` | — |
| `cancel_capture()` | — | cancela a captura |
| `recording` | — | `bool` (captura em andamento) |
| `set_hotkey(name)` / `hotkey` | — | compatibilidade: atalho de `toggle` |
| `resolve_key(name)` (função) | texto | `Combo` (compatibilidade; `ValueError` se inválido) |
