# Padrão — Feedback

## Status

- Footer: ponto + rótulo `parado` / `ativo`.
- Quando `device.active`: texto e ponto amber com glow.

## Contador e pulse-strip

- Contador LCD zera a cada start; formatação 6 dígitos.
- Barras do strip “batem” a cada incremento de contagem.

## Erros

- `last_error` do estado runtime → `#errorLabel`.
- Sem retry automático; o usuário corrige e tenta de novo.

## Estados de captura

| Estado | Feedback |
|--------|----------|
| `recording_hotkey` | Keycap `.recording` + texto “pressione uma tecla…” |
| `picking` | Botão “Capturando…” desabilitado; overlay na tela virtual |

## Overlay

- Fundo escuro semitransparente, cursor crosshair, cruz amber.
- Banner: “Capturar ponto” / clique marca XY / Esc cancela.

## Fechar → bandeja

- Modal “Ainda em execução” antes de ocultar (ver `PADRAO_modals.md`).
- Toast/balloon na bandeja após confirmar: app ainda rodando; Sair para encerrar.

## Info (i) — Assistente

- Botão circular `.info-btn` ao lado do título ou label.
- Abre **janela auxiliar** (`ui/info.html`) fora do app principal, ao lado direito quando possível.
- Bridge: `show_info_popup` / `get_info_popup` / `close_info_popup`.
- Usar para termos (L/R/M, jitter, delay, etc.) sem alongar o passo.
