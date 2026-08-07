# Feature: Hotkey configurável

## Objetivo

Permitir que o usuário grave qualquer tecla suportada como atalho global de start/stop.

## Comportamento

1. Default: `F6`.
2. Clique no keycap inicia gravação (`recording_hotkey`); o próximo key press válido vira a hotkey.
3. Clique novamente durante a gravação cancela.
4. Durante gravação ou pick location, a hotkey de toggle é ignorada.
5. Teclas suportadas: F1–F24, letras/dígitos, Space, Enter, Tab, Esc, setas, Home/End, Page Up/Down, Insert/Delete, Pause, etc.
6. O nome da tecla é persistido em `ClickConfig.hotkey` e em perfis.

## Regras

- Gravação via listener pynput separado; o listener principal continua ativo mas ignora presses enquanto `recording`.
- Hotkey inválida gera `last_error` e não altera a tecla atual.
