# DOC — core/keys.py

## Objetivo

Tabela única de teclas: nome estável ↔ código virtual (numeração VK do Win32), usada como identificador canônico em todas as plataformas por backends de input, macros, scripts, motor e hotkeys.

## Dependências

- Nenhuma além de `typing` (módulo puro, sem dependência de SO).

## Lógica central

- `normalize_name`: maiúsculas, `_` vira espaço, espaços colapsados.
- `name_to_vk`: `F1`–`F24` → `0x70…`; nomes de `_VK_NAMED` (teclas nomeadas e aliases, modificadores e variantes esquerda/direita, pontuação OEM do layout US, teclado numérico `NUM0`–`NUM9`, `NUM*`, `NUM+`, `NUM-`, `NUM.`, `NUM/`); letra ou dígito único → `ord`. Fora disso → `ValueError`.
- `vk_to_name`: caminho inverso, preferindo o nome de `_PREFERRED` (ex.: `0x0D` → `ENTER`).
- `MODIFIER_VKS` / `is_modifier_vk` / `modifier_family`: reduzem qualquer variante de modificador à família `CTRL` / `ALT` / `SHIFT` / `WIN`.
- `parse_key_sequence`: `'E'` ou `'CTRL+SHIFT+A'` → tupla de VKs na ordem de pressionamento. Cada parte é uma tecla a pressionar de verdade (modificadores incluídos). Um `+` final é tratado como parte do nome (ex.: `NUM+`).

## Assinaturas

| Função | Entrada | Saída |
|--------|---------|--------|
| `normalize_name(name)` | str | str normalizada |
| `name_to_vk(name)` | nome | `int` (ou `ValueError`) |
| `vk_to_name(vk)` | int | `str` ou `None` |
| `is_modifier_vk(vk)` | int | `bool` |
| `modifier_family(vk)` | int | `"CTRL"\|"ALT"\|"SHIFT"\|"WIN"` ou `None` |
| `parse_key_sequence(text)` | `"A"` / `"CTRL+C"` | `tuple[int, ...]` (ou `ValueError`) |
| `MODIFIER_VKS` | — | `frozenset[int]` |
