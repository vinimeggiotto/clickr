# DOC — hotkeys/combo.py

## Objetivo

Representar e analisar combinações de atalho: `'CTRL+ALT+F6'` ↔ `Combo` (módulo puro, sem dependência de SO).

## Dependências

- `core.keys` (`name_to_vk`, `vk_to_name`, `normalize_name`, `is_modifier_vk`)

## Lógica central

- `Combo` (dataclass imutável): `mods` (conjunto de famílias `CTRL` / `ALT` / `SHIFT` / `WIN`), `vk` (tecla principal) e `key` (nome de exibição).
- `str(combo)` é a forma canônica: modificadores na ordem `CTRL`, `ALT`, `SHIFT`, `WIN`, depois a tecla.
- `tokens()` devolve os identificadores de todas as teclas do combo (famílias + vk) — usado para tirar o atalho de dentro de uma macro gravada.
- `parse_combo`: divide por `+` (um `+` final faz parte do nome, ex.: `NUM+`); todas as partes menos a última precisam ser modificadores (aliases `CONTROL`, `LCTRL`, `ALTGR`, `CMD`, `SUPER`, `META`… reduzidos à família); a última é a tecla principal e **não** pode ser modificador. Inválido → `ValueError`.

## Assinaturas

| Símbolo | Entrada | Saída |
|---------|---------|--------|
| `Combo(mods, vk, key)` | — | valor imutável |
| `Combo.__str__()` | — | `"CTRL+ALT+F6"` |
| `Combo.tokens()` | — | `set` de famílias e vk |
| `make_combo(mods, vk)` | conjunto + int | `Combo` |
| `parse_combo(text)` | texto | `Combo` (ou `ValueError`) |
| `MODS` | — | ordem canônica dos modificadores |
