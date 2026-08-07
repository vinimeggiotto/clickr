# Feature: Jitter

## Objetivo

Variar aleatoriamente o intervalo entre ações para evitar timing perfeitamente periódico.

## Comportamento

- Campo: `jitter_ms` (≥ 0).
- Em cada espera do motor: `base_ms + random.randint(-jitter_ms, +jitter_ms)`, resultado mínimo 0.
- `base_ms` é `interval_ms`, ou o `delay_ms` do passo da sequência quando a sequência está ativa.
- `jitter_ms = 0` desliga a variação (espera exata).

## Regras

1. Jitter afeta apenas o **timer** do loop; não altera o número de cliques da ação.
2. Em modo burst, o jitter aplica-se aos intervalos **entre** cliques do burst; a pausa `burst_pause_ms` não recebe jitter.
3. Sem fallback nem “suavização” se o jitter for maior que o intervalo — o clamp em 0 ms é apenas limite físico da espera.
