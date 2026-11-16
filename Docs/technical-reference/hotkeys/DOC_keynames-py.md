# DOC — hotkeys/keynames.py

## Objetivo

Descrever uma tecla recebida de um listener `pynput` com nome estável, **sem importar `pynput`** (duck typing), para uso por hotkeys e pelo gravador de macros.

## Dependências

- `core.keys` (`normalize_name`, `vk_to_name`)
- `sys.platform`

## Lógica central

- Tecla especial (membro de enum, com `name` e `value`): nome normalizado (`ctrl_l` → `CTRL L`); no Windows inclui o `vk` nativo.
- Tecla de caractere (`KeyCode`):
  - caractere imprimível → nome = caractere em maiúscula, e `char` preservado;
  - no Windows, o `vk` nativo tem prioridade para o nome (`vk_to_name`), com reserva `VK<n>`;
  - fora do Windows, sem caractere, VKs de F1–F12 viram `F<n>`.
- Tecla não identificável → `None`.
- O `vk` só é devolvido no Windows, onde pynput fornece o código virtual Win32.

## Assinaturas

| Função | Entrada | Saída |
|--------|---------|--------|
| `describe_key(key)` | tecla pynput | `{"name", "vk"?, "char"?}` ou `None` |
| `format_key(key)` | tecla pynput | nome estável (`F6`, `A`, `SPACE`) ou `None` |
