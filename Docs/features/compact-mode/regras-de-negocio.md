# Feature: Modo compacto

## Objetivo

Reduzir a UI ao essencial, escondendo abas avançadas do Tier 2/3.

## Comportamento

1. Campo `compact_mode` em `ClickConfig` (bool, default `false`).
2. Quando `true`, a UI oculta as abas: **Adv**, **Macro**, **Script**, **Agenda**.
3. Permanecem: controles principais, **Run**, **Point**, **Perfis**.
4. Se a aba ativa for uma das ocultas, a UI volta para **Run**.
5. Persistido em perfis via `to_dict` / `from_dict`.
6. Bridge: `set_compact_mode(enabled)` ou `set_config({ compact_mode })`.

## UI

Toggle na aba **Run** (“Modo compacto”), sempre visível.
