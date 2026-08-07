# Feature: Pick location

## Objetivo

Capturar coordenadas de tela (XY) para o modo ponto fixo via overlay cobrindo a tela virtual.

## Comportamento

1. UI chama `pick_location` → abre `ui/overlay.html` em janela frameless on-top com geometria da **tela virtual** (`SM_*VIRTUALSCREEN`: x, y, width, height), cobrindo todos os monitores.
2. Clique no overlay confirma: Python lê a posição real do cursor (`GetCursorPos`) e grava `fixed_x` / `fixed_y`, com `position_mode = fixed`.
3. `Esc` cancela sem alterar a configuração.
4. Estado `picking` fica `true` enquanto o overlay está aberto.

## Regras

- A fonte de verdade das coordenadas é o cursor do SO no momento do clique, não `screenX/Y` do browser.
- Não se usa `fullscreen=True` do pywebview (isso limita a um monitor); a janela é dimensionada explicitamente na tela virtual.
- Não há retry se o overlay falhar ao abrir; erro propaga à UI.
