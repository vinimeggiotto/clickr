# DOC — window_filter/filter.py

## Objetivo

Decidir se o motor pode agir com base na janela em foco (processo/app e/ou substring do título), em Windows, macOS e Linux, e identificar janelas do próprio Clickr.

## Dependências

- `core.types.WindowFilterConfig`
- Windows: Win32 `GetForegroundWindow`, título, `QueryFullProcessImageNameW`, `WindowFromPoint`, `GetAncestor`, `GetWindowThreadProcessId`
- macOS: `osascript` + System Events
- Linux: `xprop` (obrigatório com filtro ativo); `xdotool` opcional para título

## Lógica central

- `allows()`: se desligado ou sem critérios → `True`.
- Com critérios: obtém processo/app + título da janela foreground; exige AND dos critérios não vazios.
- **Cache:** fora do Windows a consulta abre subprocessos, então `allows()` reaproveita o resultado por `_FOREGROUND_CACHE_TTL_S` (0,25 s). No Windows consulta sempre. `foreground_info()` lê sem cache (usado em "usar janela atual").
- Match de processo: case-insensitive; aceita com ou sem `.exe` (útil no Windows).
- macOS: compara nome do app (System Events), não necessariamente o bundle id.
- Linux: `WM_CLASS` (instância) como “processo”; título via xdotool ou `_NET_WM_NAME`/`WM_NAME`.
- Sem `xprop` / sem `osascript` / falha da ferramenta → `OSError` (motor grava `last_error` e para). Não libera o clique.
- **Janela própria** (funções de módulo, só Windows; nos demais SOs devolvem `None` e o chamador usa outro critério):
  - `point_in_own_window(x, y)`: a janela raiz sob o ponto pertence a este processo;
  - `foreground_is_own_window()`: a janela em foco pertence a este processo.

## Assinaturas

| Símbolo | Entrada | Saída |
|---------|---------|--------|
| `configure(config)` | `WindowFilterConfig` | — |
| `get_config()` | — | `WindowFilterConfig` |
| `allows()` | — | `bool` (ou `OSError`) |
| `foreground_info()` | — | `(processo \| None, título)` sem cache (ou `OSError`) |
| `point_in_own_window(x, y)` (função) | pixels de tela | `bool`, ou `None` fora do Windows |
| `foreground_is_own_window()` (função) | — | `bool`, ou `None` fora do Windows |
