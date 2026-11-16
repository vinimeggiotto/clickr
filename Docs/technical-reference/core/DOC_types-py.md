# DOC — core/types.py

## Objetivo

Definir o contrato de configuração de clique (`ClickConfig`, `WindowFilterConfig`, `SequenceStep`) e o estado runtime (`RuntimeState`) serializáveis para a bridge JS, além das constantes do formato de perfil.

## Dependências

- `dataclasses`, `typing` (stdlib)

## Lógica central

- `ClickConfig` guarda **só configuração de clique** (é o que um perfil v2 grava). `hotkey`, `always_on_top` e `compact_mode` foram removidos: são preferências em `app.settings`.
- Campos: `interval_ms`, `jitter_ms`, `button`, `click_type`, `position_mode`, `fixed_x`, `fixed_y`, `hold`, `start_delay_ms`, `max_clicks`, `max_duration_ms`, `burst_count`, `burst_pause_ms`, `sequence`, `window_filter`.
- Campos adicionados na 1.1 (padrões = comportamento da 1.0): `restore_cursor` (`False`), `position_jitter_px` (`0`, limitado a `MAX_POSITION_JITTER_PX = 500`), `action` (`"mouse"` | `"key"`), `key_name` (`"SPACE"`).
- `from_dict` mescla só chaves conhecidas (chaves extras, como as legadas, são ignoradas); `None` em campo obrigatório equivale a ausente; `max_*` / `burst_count` vazios/≤0 viram `null`; `burst_pause_ms` aceita 0; `button` / `click_type` / `position_mode` / `action` inválidos voltam ao padrão; `key_name` é normalizado para maiúsculas.
- `sequence` é lista de `{x,y,delay_ms}`; `window_filter` é objeto aninhado.
- Constantes de perfil: `PROFILE_VERSION = 2`; `LEGACY_APP_KEYS = ("hotkey", "always_on_top", "compact_mode")`; `V1_CONFIG_KEYS` = campos de clique que já existiam no formato v1.
- `RuntimeState` ganhou `phase`, `starts_at`, `elapsed_ms`, `actual_cps`, `sequence_index`, `blocked`. `to_dict()` embute `config` e arredonda `actual_cps` a 1 casa; `last_error` aceita qualquer objeto (o controller normaliza). `picking` / `recording_hotkey` são preenchidos pelo controller.

## Assinaturas

| Tipo / método | Entrada | Saída |
|---------------|---------|--------|
| `ClickConfig(...)` | campos opcionais | instância |
| `ClickConfig.to_dict()` / `from_dict(data)` | — / dict | dict / instância |
| `ClickConfig.clamped_interval_ms()` | — | `int ≥ 1` |
| `ClickConfig.clamped_jitter_ms()` | — | `int ≥ 0` |
| `ClickConfig.clamped_start_delay_ms()` | — | `int ≥ 0` |
| `ClickConfig.has_sequence()` | — | `bool` |
| `WindowFilterConfig.to_dict()` / `from_dict` | — / Any | dict / instância |
| `SequenceStep.to_dict()` / `from_dict` | — / Any | dict / instância (`ValueError` se não for dict) |
| `RuntimeState.to_dict()` | — | dict de estado |
| `PROFILE_VERSION` / `LEGACY_APP_KEYS` / `V1_CONFIG_KEYS` / `MAX_POSITION_JITTER_PX` | — | constantes |
