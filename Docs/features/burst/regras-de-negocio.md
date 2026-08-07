# Feature: Burst

## Objetivo

Emitir rajadas de N cliques e pausar entre rajadas.

## Configuração

| Campo | Significado |
|-------|-------------|
| `burst_count` | `null` = desligado (1 clique por ciclo). Inteiro ≥ 1 = tamanho da rajada |
| `burst_pause_ms` | Pausa após completar a rajada (`null` ou 0 = sem pausa extra) |

## Comportamento

1. Com burst ligado: realiza `burst_count` tentativas de clique; entre elas espera `interval_ms ± jitter` (ou delay do passo da sequência).
2. Após a rajada: espera apenas `burst_pause_ms` (sem reaplicar o intervalo).
3. Com burst desligado: 1 clique + espera `interval_ms ± jitter` (fluxo normal).
4. Limites (`max_clicks` / duração) e stop interrompem no meio da rajada.
5. Filtro de janela pode pular cliques individuais dentro da rajada.
