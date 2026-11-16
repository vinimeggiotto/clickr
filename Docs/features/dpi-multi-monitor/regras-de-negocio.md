# Feature: DPI awareness e multi-monitor

## Objetivo

Garantir coordenadas de tela corretas em monitores múltiplos e escalas DPI diferentes.

## Comportamento

1. No startup (`main.py`), chama `SetProcessDpiAwarenessContext(PER_MONITOR_AWARE_V2)` (no-op fora do Windows).
2. Movimento/clique absoluto usa métricas da **tela virtual** (`SM_*VIRTUALSCREEN`) e flags `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK`.
3. Se o contexto DPI já estiver definido no processo (erro Win32 5), a chamada é tratada como concluída.
4. Se a chamada falhar por outro motivo (`OSError`), `main.py` registra o erro em `clickr.log` e o aplicativo segue abrindo.

## Regras

- Sem fallback para APIs DPI legadas (`SetProcessDPIAware` / shcore) se a API moderna falhar.
- Pick location, ponto fixo, sequência e posição salva da janela compartilham o mesmo sistema de coordenadas (tela virtual).
- A última posição da janela principal só é restaurada se ainda cair dentro da tela virtual atual.
