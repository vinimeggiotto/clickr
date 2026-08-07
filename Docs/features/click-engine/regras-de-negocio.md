# Feature: Motor de clique (click-engine)

## Objetivo

Gerar cliques de mouse no sistema operacional Windows em intervalo configurável, controlados pela UI e pela hotkey global.

## Escopo (núcleo + Tier 1 + Tier 2)

| Capacidade | Comportamento |
|------------|----------------|
| Botão | Esquerdo, direito, meio, 4 (XBUTTON1), 5 (XBUTTON2) |
| Tipo | Simples, duplo ou hold (pressiona ao iniciar, solta ao parar) |
| Intervalo | `interval_ms` ≥ 1; CPS na UI = `1000 / interval_ms` |
| Jitter | Espera = `base ± jitter_ms` (uniforme), nunca negativa |
| Posição cursor | Clique na posição atual do ponteiro |
| Posição ponto fixo | Clique absoluto em `(fixed_x, fixed_y)` na tela virtual |
| Sequência | Se `sequence` não vazia, cicla XY + `delay_ms` por passo |
| Burst | Se `burst_count` definido: N cliques com intervalo entre eles, depois `burst_pause_ms` |
| Filtro de janela | Antes de cada clique, `WindowFilter.allows()`; se False, **pula** o clique |
| Delay de início | Aguarda `start_delay_ms` antes do primeiro tick |
| Limite de cliques | Para ao atingir `max_clicks` (se definido) |
| Duração máxima | Para ao atingir `max_duration_ms` desde o fim do delay (se definido) |
| Start/stop | Botão pulse na UI e hotkey global configurável |
| Contador | Incrementa a cada ação (duplo conta 2; hold conta 1 no press; pulado pelo filtro não conta) |

## Regras

1. O loop de clique roda em **thread dedicada**; a UI apenas observa estado.
2. Parada: UI, hotkey, limite N, duração máxima; hold libera o botão ao parar.
3. Erros de `SendInput` são expostos em `last_error` e interrompem o loop — sem retry silencioso.
4. Alterar configuração com o motor ativo aplica no próximo tick (sem reset obrigatório do contador).
5. Em hold, após o press inicial o loop só observa stop/duração (não re-clica).
6. Clique pulado pelo filtro **não** avança a sequência.
7. Coordenadas absolutas usam `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK` (multi-monitor).

## Fora do escopo desta feature

Macro, scheduler, script DSL, compact mode (Tier 3).
