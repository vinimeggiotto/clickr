# Padrão — Inputs

## LCD number/text

- Container `.lcd-input` (groove + inset shadow).
- Valor em amber (números) ou `--text` (nome de perfil).
- Sufixo à direita (`ms`, `n`) em `--text-dim`.
- Variante `.compact` para grade Run/Point.

## Fader (range)

- Trilha 4px groove; thumb circular amber 14px.
- Espelha o campo numérico de intervalo.

## Select de perfis

- `.profile-select`: groove, sem borda, lista compacta (`size="4"`).
- Duplo clique carrega o perfil selecionado.

## Select de idioma (nameplate)

- `.locale-select`: compacto (altura ~22px), groove, borda amber sutil, `text-transform: none`.
- Opções com rótulo autônimo + região (ex.: `Português (Brasil)`, `English (United States)`).
- Valor = código BCP-47 (`pt-BR`, `en-US`, …); alinhado à direita do nameplate.
- `aria-label` via `data-i18n-aria="localeSelect.aria"`.

## Campos Tier 1 + Tier 2

| Campo | Tipo | Vazio significa |
|-------|------|-----------------|
| Delay início | number ≥ 0 | 0 ms |
| Jitter ± | number ≥ 0 | sem variação |
| Limite cliques | number opcional | sem limite (`null`) |
| Duração máx. | number opcional | sem limite (`null`) |
| X / Y | number | ponto fixo atual |
| Delay passo (sequência) | number ≥ 0 | 0 ms no novo passo |
| Processo / título (filtro) | text | critério ausente |
| Burst N | number opcional | burst desligado |
| Pausa burst | number opcional ≥ 0 | sem pausa extra |
| Nome do perfil | text ≤ 64 | obrigatório ao salvar |

## Lista de sequência

- Container `.seq-list` (groove); itens monoespaçados amber + botão remover.
- Ações `.action-btn.tiny` no cabeçalho da sequência.

## Validação visual

Erros de bridge/perfil aparecem em `.error` (não em toast).
