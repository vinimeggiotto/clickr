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
4. Hold ignora a sequência (usa ponto fixo/cursor como no Tier 1). A ação de teclado também ignora.
5. Clique pulado (filtro de janela ou proteção da própria janela) **não** avança o índice.
6. `position_jitter_px` e `restore_cursor` valem para os passos da sequência.
7. O estado expõe `sequence_index` (passo do próximo clique); a UI destaca esse item na lista enquanto o motor roda.
8. Ao iniciar o motor, o índice volta ao primeiro passo.

## Bridge

| Método | Papel |
|--------|--------|
| `add_sequence_point(x?, y?, delay_ms=0)` | acrescenta passo (XY do cursor se omitidos) |
| `pick_location("sequence", delay_ms)` | captura na tela e acrescenta à lista |
| `update_sequence_point(index, {x?, y?, delay_ms?})` | edita um passo |
| `move_sequence_point(index, to)` | muda a posição de um passo na lista |
| `remove_sequence_point(index)` | remove um passo |
| `clear_sequence()` | esvazia a lista |

Índice fora da lista → erro `sequence.badIndex`; valor não numérico no patch → `config.invalid`.

## UI

Aba **Point**:

- **capturar**: escolhe o ponto na tela e já o coloca na lista.
- **+ X/Y**: acrescenta as coordenadas dos campos X e Y acima.
- **limpar**: esvazia a lista.
- Campo de delay (ms) usado para os novos pontos.
- Cada item mostra XY, delay editável na própria linha, botões ↑ / ↓ para reordenar e × para remover.
