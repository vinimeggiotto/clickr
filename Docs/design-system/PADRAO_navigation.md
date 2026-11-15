# Padrão — Navigation

## Rail de abas (lateral)

- Container `.tabs` à esquerda do `.workspace`, `aria-orientation="vertical"`.
- Largura fixa **96px**, fundo groove, itens empilhados.
- `.tab`: uppercase, letter-spacing, padding vertical generoso, alinhamento à esquerda.
- Ativo: mesmo tratamento do segmented (gradiente + amber).
- Modo compacto: `.tab-adv` oculto.
- **Manual** e **Atalhos** ficam no rail principal (não são avançados).
- Ordem: Clique, Run, Point, Perfis, Atalhos, Manual, Adv, Macro, Script, Agenda.
- Acessibilidade: cada `.tab` tem `id` + `aria-controls` e cada painel `aria-labelledby`; só a aba ativa entra na ordem do Tab (tabindex itinerante); setas, Home e End percorrem as abas visíveis.

## Manual (painel)

- Toggle **Guia | Assistente** (`.manual-modes` segmented) no topo do painel.
- Guia: progresso `N / total`, corpo com scroll fino, Anterior/Próximo, Experimentar opcional.
- Assistente: mesmos tokens; controles (segmented, lcd, fader) dentro do corpo; no fim, Só salvar / Salvar e ativar.
- (i) informativo nos títulos/labels → janela `info.html` fora do app (ver `PADRAO_feedback.md`).

## Não usar

- Abas horizontais no topo do miolo (legado deste app).
- Bottom nav com ícones (espaço insuficiente no device).
