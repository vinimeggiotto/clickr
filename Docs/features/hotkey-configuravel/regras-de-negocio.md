# Feature: Hotkey configurável

## Objetivo

Permitir que o usuário grave o atalho global de start/stop.

> A partir da 1.1 esta feature faz parte de **Atalhos** (um atalho por ação, combinações com modificadores e modo "segurar"). As regras completas estão em [`atalhos`](../atalhos/regras-de-negocio.md); este documento registra apenas o que mudou em relação à 1.0.x.

## Comportamento

1. Default do atalho de iniciar/parar: `F6` (inalterado).
2. O keycap do rodapé continua gravando o atalho de iniciar/parar; a aba **Atalhos** oferece o mesmo e as demais ações.
3. Além de tecla única, aceita combinações (`CTRL+ALT+F6`). `Esc` sozinho cancela a gravação.
4. O atalho deixou de ser `ClickConfig.hotkey`: agora é a preferência `hotkeys.toggle` em `settings.json`.
5. Perfis v2 não guardam atalho. Perfis da 1.0.x com `hotkey` ainda aplicam esse valor ao atalho de iniciar/parar quando carregados.

## Regras

- `set_config({ hotkey })` ainda é aceito e encaminhado ao atalho de iniciar/parar.
- Hotkey inválida gera `last_error` (`hotkey.unsupported`) e não altera a tecla atual.
- O atalho de iniciar/parar não pode ficar vazio (`hotkey.toggleRequired`).
