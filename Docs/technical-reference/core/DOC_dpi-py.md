# DOC — core/dpi.py

## Objetivo

Ativar DPI awareness per-monitor V2 no processo antes de criar janelas ou ler coordenadas.

## Dependências

- `ctypes`, `sys` (stdlib)
- `user32.SetProcessDpiAwarenessContext`

## Lógica central

- Chama `SetProcessDpiAwarenessContext(-4)` (`PER_MONITOR_AWARE_V2`).
- Sucesso → retorna.
- Erro Win32 `5` (ACCESS_DENIED, contexto já definido) → retorna.
- Qualquer outro erro → `OSError`.

## Assinaturas

| Função | Entrada | Saída |
|--------|---------|--------|
| `enable_dpi_awareness()` | — | `None` (ou levanta `OSError`) |
