# Feature: Sequência multi-ponto

## Objetivo

Clicar em uma lista cíclica de coordenadas, cada uma com delay próprio.

## Modelo

```json
"sequence": [
  { "x": 100, "y": 200, "delay_ms": 80 },
  { "x": 300, "y": 400, "delay_ms": 120 }
]
```

## Comportamento

1. Lista vazia → motor usa `position_mode` (cursor ou ponto fixo).
2. Lista não vazia → cada ação usa o passo atual; após clique bem-sucedido, avança (wrap).
3. `delay_ms` do passo substitui `interval_ms` como base da espera pós-clique (ainda com jitter).
4. Hold ignora a sequência (usa ponto fixo/cursor como no Tier 1).
5. Clique pulado pelo filtro de janela **não** avança o índice.

## UI

Aba **Point**: editor compacto (+ ponto / limpar / remover item). “+ ponto” usa o XY do ponto fixo se o modo for PONTO FIXO; senão a posição atual do cursor.
