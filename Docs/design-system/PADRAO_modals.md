# Padrão — Modals

## Uso

Diálogos sobre o `app-shell` para confirmação ou aviso pontual (ex.: fechar → bandeja).

## Estrutura

- `.modal` — overlay semitransparente (`rgba(10,8,6,0.72)`), `position: absolute` no shell, z-index acima do device e abaixo do splash se necessário.
- `.modal-card` — painel amber/dark, radius 14px, borda amber suave.
- `.modal-title` — uppercase, letter-spacing, cor `--amber`.
- `.modal-body` — texto 12px; variante `.dim` para secundário.
- `.modal-actions` — grid 2 colunas com `.action-btn` / `.ghost`.

## Comportamento

- Atributo `hidden` no `.modal` controla visibilidade.
- Clique no backdrop pode cancelar (não confirma ação destrutiva sem botão).
- Foco inicial no botão primário ao abrir.

## Gate de idioma (pós-splash)

- `#localeGate` / `.locale-gate` — overlay no `app-shell` (z-index abaixo do splash, acima do device).
- Card amber com título, subtítulo e lista de botões `.locale-gate-btn` (um por locale).
- Confirmação imediata ao clicar (sem segundo passo); não é o mesmo componente `.modal`, mas compartilha tokens visuais.
