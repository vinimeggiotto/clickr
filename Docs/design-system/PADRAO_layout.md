# Padrão — Layout

## Tokens de casca

| Token | Valor | Uso |
|-------|--------|-----|
| `--bg` | `#14100c` | Fundo da janela |
| `--panel` / `--panel-raised` | `#1d1712` / `#241c15` | Corpo do device |
| `--groove` | `#0e0b08` | Cavidades (stage, inputs, segmented) |
| `--radius` | `14px` | Stage e cantos principais |
| Device | máx. `448px` | Janela ~468×676 |
| Rail abas | `96px` | Nav vertical à esquerda |

## Composição

1. **Title bar custom** — janela `frameless`; logo + “Clickr” (drag) à esquerda; minimizar / fechar amber minimal à direita (sem maximizar).
2. **Splash** — ao abrir, `#splash` com `clickr_logo_horizontal.svg` + barra indeterminada até a bridge estar pronta (`body.booting`); mínimo ~1,1s.
3. **Locale gate** — se não houver `locale` em settings, `#localeGate` (overlay amber no `app-shell`) após o splash; escolha obrigatória.
4. **Nameplate** — ícone `clickr_icon.svg` à esquerda; à direita `#localeSelect`.
5. **Stage** — pulse button compacto, contador LCD, pulse-strip (casca fixa).
6. **Workspace** — rail de abas à **esquerda** (vertical) + coluna de painel à direita.
7. **Um painel por vez**:
   - **Clique** — intervalo, L/R/M/4/5, tipo, cursor/ponto fixo
   - **Run** — delay, jitter, limites, always-on-top, compact
   - **Point** — XY, capturar, sequência
   - **Perfis / Manual / Adv / Macro / Script / Agenda** — Manual é guia interativo
8. **Footer** — keycap da hotkey + status (casca fixa).
9. **Modo compacto** — oculta `.tab-adv`; se aba avançada ativa, volta para **Clique** (Manual permanece).

## Regras

- Uma composição: o viewport é o device amber, não um painel de métricas.
- `.controls`, `.workspace` e `.panels` usam `overflow: hidden` — **sem scrollbar** na casca.
- Rail `.tabs`: coluna 96px; overflow vertical sem barra visível se as abas excederem a altura.
- Exceção: lista de sequência (conteúdo dinâmico) pode rolar com thumb fino.
- Overlay de captura (`overlay.html`) cobre a **tela virtual** (todos os monitores), fora do device.
