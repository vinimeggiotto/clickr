# Feature: Pick location

## Objetivo

Capturar coordenadas de tela (XY) para o ponto fixo ou para a sequência, via overlay cobrindo a tela virtual ou via atalho global.

## Comportamento

1. UI chama `pick_location(target, delay_ms)` → abre `ui/overlay.html` em janela frameless, on-top e **transparente**, com a geometria da **tela virtual** (x, y, width, height), cobrindo todos os monitores. O usuário enxerga o que está por baixo enquanto escolhe.
2. Clique no overlay confirma (`confirm_pick`): Python lê a posição real do cursor e:
   - `target = "fixed"` (padrão): grava `fixed_x` / `fixed_y`, com `position_mode = fixed`;
   - `target = "sequence"`: acrescenta `{x, y, delay_ms}` ao fim da sequência (com o delay informado na chamada).
3. `Esc` cancela (`cancel_pick`) sem alterar a configuração.
4. Estado `picking` fica `true` enquanto o overlay está aberto. Chamar `pick_location` de novo nesse período não abre outro overlay.
5. Se o overlay for fechado por outra via (Alt+F4, SO), `picking` volta a `false`.
6. Atalho **Capturar ponto no cursor** (`pick_point`, sem padrão): grava a posição atual do cursor como ponto fixo, sem abrir overlay.

## Regras

- A fonte de verdade das coordenadas é o cursor do SO no momento do clique, não `screenX/Y` do browser.
- Não se usa `fullscreen=True` do pywebview (isso limita a um monitor); a janela é dimensionada explicitamente na tela virtual.
- Não há retry se o overlay falhar ao abrir; o erro vai para `last_error` (`overlayMissing` se o arquivo não existir).
- Com o overlay aberto, os atalhos de iniciar/parar, capturar ponto e gravar macro são ignorados; **Parar tudo** fecha o overlay.

## UI

Aba **Point**: **Capturar ponto** (ponto fixo) e **capturar** na barra da sequência (ponto direto para a lista).
