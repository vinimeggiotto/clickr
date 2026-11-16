# DOC — core/sendinput_null.py

## Objetivo

Backend de input que **não toca no SO**: registra cada chamada em memória. Usado nos testes automatizados e em ambientes sem display.

## Dependências

- `core.keys.name_to_vk`
- `threading` (stdlib)

## Lógica central

- Selecionado por `core.sendinput` quando `CLICKR_INPUT_BACKEND=null`.
- Mantém `calls` (lista de tuplas) protegida por lock, um cursor simulado (inicia em `(0, 0)`) e tela virtual fixa `(0, 0, 1920, 1080)`.
- Entradas registradas: `("move", x, y)`, `("down"|"up"|"click", botão)`, `("scroll", dy, dx)`, `("key_down"|"key_up", vk)`, `("char_down"|"char_up", char)`, `("type", texto)`.
- `move_absolute` atualiza o cursor simulado; `click_at` registra movimento + `count` cliques e, com `restore=True`, o movimento de volta.
- Botão inválido → `ValueError`.

## Assinaturas

Mesma superfície pública de `core.sendinput` (ver `DOC_sendinput-py.md`), mais os auxiliares de teste:

| Função | Papel |
|--------|--------|
| `reset()` | limpa as chamadas e zera o cursor |
| `recorded() -> list[tuple]` | cópia das chamadas registradas |
| `set_cursor_pos_for_test(x, y)` | define o cursor simulado sem registrar chamada |
