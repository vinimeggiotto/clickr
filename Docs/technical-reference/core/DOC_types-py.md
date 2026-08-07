# DOC — core/types.py

## Objetivo

Definir o contrato de configuração (`ClickConfig`, `WindowFilterConfig`, `SequenceStep`) e o estado runtime (`RuntimeState`) serializáveis para a bridge JS.

## Dependências

- `dataclasses`, `typing` (stdlib)

## Lógica central

- Campos Tier 2: `jitter_ms`, `burst_count`, `burst_pause_ms`, `sequence`, `window_filter`; botões `x1`/`x2`.
- Campos Tier 3 UI: `compact_mode` (bool).
- `from_dict` mescla só chaves conhecidas; `max_*` / `burst_count` vazios/≤0 viram `null`; `burst_pause_ms` aceita 0.
- `sequence` é lista de `{x,y,delay_ms}`; `window_filter` é objeto aninhado.
- `RuntimeState.to_dict()` embute `config`; flags UI `picking` / `recording_hotkey` são preenchidas pelo controller.

## Assinaturas

| Tipo / método | Entrada | Saída |
|---------------|---------|--------|
| `ClickConfig(...)` | campos opcionais | instância |
| `ClickConfig.to_dict()` / `from_dict(data)` | — / dict | dict / instância |
| `ClickConfig.clamped_interval_ms()` | — | `int ≥ 1` |
| `ClickConfig.clamped_jitter_ms()` | — | `int ≥ 0` |
| `ClickConfig.has_sequence()` | — | `bool` |
| `WindowFilterConfig.to_dict()` / `from_dict` | — / Any | dict / instância |
| `SequenceStep.to_dict()` / `from_dict` | — / Any | dict / instância |
| `RuntimeState.to_dict()` | — | dict de estado |
