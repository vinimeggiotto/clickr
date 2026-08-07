# DOC — window_filter/filter.py

## Objetivo

Decidir se o motor pode clicar com base na janela em foco (processo/app e/ou substring do título), em Windows, macOS e Linux.

## Dependências

- `core.types.WindowFilterConfig`
- Windows: Win32 `GetForegroundWindow`, título, `QueryFullProcessImageNameW`
- macOS: `osascript` + System Events
- Linux: `xprop` (obrigatório com filtro ativo); `xdotool` opcional para título

## Lógica central

- `allows()`: se desligado ou sem critérios → `True`.
- Com critérios: obtém processo/app + título da janela foreground; exige AND dos critérios não vazios.
- Match de processo: case-insensitive; aceita com ou sem `.exe` (útil no Windows).
- macOS: compara nome do app (System Events), não necessariamente o bundle id.
- Linux: `WM_CLASS` (instância) como “processo”; título via xdotool ou `_NET_WM_NAME`/`WM_NAME`.
- Sem `xprop` / sem `osascript` / falha da ferramenta → `OSError` (motor grava `last_error` e para). Não libera o clique.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `configure(config)` | `WindowFilterConfig` | — |
| `get_config()` | — | `WindowFilterConfig` |
| `allows()` | — | `bool` (ou `OSError`) |
