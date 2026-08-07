# Feature: DPI awareness e multi-monitor

## Objetivo

Garantir coordenadas de tela corretas em monitores múltiplos e escalas DPI diferentes.

## Comportamento

1. No startup (`main.py`), chama `SetProcessDpiAwarenessContext(PER_MONITOR_AWARE_V2)`.
2. Movimento/clique absoluto usa métricas da **tela virtual** (`SM_*VIRTUALSCREEN`) e flags `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK`.
3. Se o contexto DPI já estiver definido no processo (erro Win32 5), a chamada é tratada como concluída.

## Regras

- Sem fallback para APIs DPI legadas (`SetProcessDPIAware` / shcore) se a API moderna falhar por outro motivo — a falha propaga.
- Pick location e ponto fixo compartilham o mesmo sistema de coordenadas.
