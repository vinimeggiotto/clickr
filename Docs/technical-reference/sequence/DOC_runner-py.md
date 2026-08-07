# DOC — sequence/runner.py

## Objetivo

Manter o índice cíclico da lista de passos XY e expor o alvo do próximo clique.

## Dependências

- `core.types.SequenceStep`

## Lógica central

- `peek()` devolve `SequenceTarget(x, y, delay_ms, index)` sem avançar.
- `advance()` incrementa o índice com wrap.
- `reset(steps)` redefine a lista e zera o índice (usado no `start` do engine).
- Lista vazia → `peek()` retorna `None` / `is_active()` é `False`.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `reset(steps=None)` | lista opcional | — |
| `set_steps(steps)` | `list[SequenceStep]` | — |
| `is_active()` | — | `bool` |
| `peek()` | — | `SequenceTarget \| None` |
| `advance()` | — | — |
| `current_index()` | — | `int` |
