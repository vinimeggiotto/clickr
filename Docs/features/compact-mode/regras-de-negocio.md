# Feature: Modo compacto

## Objetivo

Reduzir a UI ao essencial, escondendo abas avançadas do Tier 2/3.

## Comportamento

1. Preferência do aplicativo `compact_mode` (bool, default `false`) em `settings.json` — **não** faz mais parte de `ClickConfig`.
2. Quando `true`, a UI oculta as abas: **Adv**, **Macro**, **Script**, **Agenda**.
3. Permanecem: **Clique**, **Run**, **Point**, **Perfis**, **Atalhos**, **Manual**.
4. Se a aba ativa for uma das ocultas, a UI volta para **Clique**.
5. Vale entre sessões (é lido de `settings.json` no boot).
6. Bridge: `set_preferences({ compact_mode })` (usado pela UI) ou `set_compact_mode(enabled)`. `set_config({ compact_mode })` ainda é aceito e encaminhado às preferências.
7. Perfis no formato atual (v2) não guardam nem alteram o modo compacto. Perfis da 1.0.x que trazem `compact_mode` continuam aplicando o valor ao serem carregados (ver [`perfis`](../perfis/regras-de-negocio.md)).

## UI

Toggle na aba **Run** (“Modo compacto”), sempre visível.
