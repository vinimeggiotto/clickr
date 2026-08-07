# DOC — window_filter/filter.py

## Objetivo

Decidir se o motor pode clicar com base na janela em foco (processo e/ou substring do título).

## Dependências

- `core.types.WindowFilterConfig`
- Win32: `GetForegroundWindow`, `GetWindowTextW`, `GetWindowThreadProcessId`, `OpenProcess`, `QueryFullProcessImageNameW`

## Lógica central

- `allows()`: se desligado ou sem critérios → `True`.
- Com critérios: lê título e/ou basename do executável da janela foreground; exige AND dos critérios não vazios.
- Match de processo aceita `nome` ou `nome.exe` (case-insensitive).

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `configure(config)` | `WindowFilterConfig` | — |
| `get_config()` | — | `WindowFilterConfig` |
| `allows()` | — | `bool` |
