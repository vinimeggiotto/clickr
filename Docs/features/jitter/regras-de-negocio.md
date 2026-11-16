# Feature: Jitter

## Objetivo

Variar aleatoriamente o intervalo entre ações (e, opcionalmente, a posição do clique) para evitar um padrão perfeitamente periódico.

## Comportamento — tempo

- Campo: `jitter_ms` (≥ 0).
- Em cada espera do motor: `base_ms + random.randint(-jitter_ms, +jitter_ms)`, resultado mínimo 0.
- `base_ms` é `interval_ms`, ou o `delay_ms` do passo da sequência quando a sequência está ativa.
- `jitter_ms = 0` desliga a variação (espera exata).

## Comportamento — posição

- Campo: `position_jitter_px` (0–500; valores fora da faixa são limitados no parse).
- A cada clique em **ponto fixo** ou em **passo da sequência**, soma um deslocamento inteiro uniforme em `[-N, +N]` a X e a Y, sorteados de forma independente.
- No modo **cursor** não se aplica (o cursor é do usuário). Na ação de teclado também não.
- `0` desliga (clique exatamente no ponto).

## Regras

1. O jitter de tempo afeta apenas o **timer** do loop; não altera o número de cliques da ação.
2. Em modo burst, o jitter aplica-se aos intervalos **entre** cliques do burst; a pausa `burst_pause_ms` não recebe jitter.
3. Sem fallback nem “suavização” se o jitter for maior que o intervalo — o clamp em 0 ms é apenas limite físico da espera.
4. A proteção da própria janela avalia o ponto **já deslocado**.

## UI

`jitter_ms` na aba **Run**; `position_jitter_px` na aba **Point**.
