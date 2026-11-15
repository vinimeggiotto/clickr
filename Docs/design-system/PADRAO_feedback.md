# Padrão — Feedback

## Status

- Footer: ponto + rótulo `parado` / `ativo` / `gravando` / `macro` / `script`.
- Quando `device.active`: texto e ponto amber com glow.
- Contagem do delay inicial (`device.counting`): rótulo `aguardando` e segundos restantes dentro do botão pulse.
- Ação pulada (`device.blocked`): rótulo `alvo sobre o Clickr` ou `fora da janela do filtro`.
- Selo de versão nova no footer (`#updateBadge`) quando o estado traz `update`.

## Contador e pulse-strip

- Contador LCD zera a cada start; formatação 6 dígitos.
- Barras do strip “batem” a cada incremento de contagem.
- Sob o contador (`#liveStats`): tempo decorrido e taxa real de cliques por segundo.

## Erros

- `last_error` do estado runtime (`{code, message, params}`) → `#errorLabel` (`role="alert"`), traduzido pela chave `errors.<code>` do catálogo ativo; sem tradução, mostra `message`.
- Mensagens geradas na própria UI (validação, falha da bridge) usam o mesmo rótulo e somem sozinhas após alguns segundos.
- Sem retry automático; o usuário corrige e tenta de novo.

## Estados de captura

| Estado | Feedback |
|--------|----------|
| `recording_hotkey` | Keycap `.recording` da ação em gravação (`recording_hotkey_action`) + texto “pressione uma tecla…” |
| `window_capture.active` | Botão “Usar janela atual” em `.recording` com contagem regressiva |
| `picking` | Botão “Capturando…” desabilitado; overlay na tela virtual |

## Overlay

- Fundo escuro semitransparente, cursor crosshair, cruz amber.
- Banner: “Capturar ponto” / clique marca XY / Esc cancela.

## Fechar → bandeja

- Modal “Ainda em execução” antes de ocultar (ver `PADRAO_modals.md`).
- Toast/balloon na bandeja após confirmar (apenas na primeira vez): app ainda rodando; Sair para encerrar.

## Info (i) — Assistente

- Botão circular `.info-btn` ao lado do título ou label.
- Abre **janela auxiliar** (`ui/info.html`) fora do app principal, ao lado direito quando possível.
- Bridge: `show_info_popup` / `get_info_popup` / `close_info_popup`.
- Usar para termos (L/R/M, jitter, delay, etc.) sem alongar o passo.
