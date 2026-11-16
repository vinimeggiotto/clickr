# Feature: Motor de clique (click-engine)

## Objetivo

Repetir uma ação de mouse (ou de teclado) no sistema operacional em intervalo configurável, controlada pela UI, pelos atalhos globais, pela bandeja e pela agenda.

## Escopo (núcleo + Tier 1 + Tier 2)

| Capacidade | Comportamento |
|------------|----------------|
| Ação | `action = mouse` (padrão) ou `key` (ver [`autoclique-teclado`](../autoclique-teclado/regras-de-negocio.md)) |
| Botão | Esquerdo, direito, meio, 4 (XBUTTON1), 5 (XBUTTON2) |
| Tipo | Simples, duplo ou hold (pressiona ao iniciar, solta ao parar) |
| Intervalo | `interval_ms` ≥ 1; CPS estimado na UI = `1000 / interval_ms` |
| Jitter | Espera = `base ± jitter_ms` (uniforme), nunca negativa |
| Posição cursor | Clique na posição atual do ponteiro |
| Posição ponto fixo | Clique absoluto em `(fixed_x, fixed_y)` na tela virtual |
| Jitter de posição | `position_jitter_px` (0–500): desloca ponto fixo / passo da sequência em ±N px por eixo; não se aplica ao modo cursor |
| Restaurar cursor | `restore_cursor`: após clicar em ponto fixo / passo da sequência, o cursor volta para onde estava |
| Sequência | Se `sequence` não vazia, cicla XY + `delay_ms` por passo |
| Burst | Se `burst_count` definido: N cliques com intervalo entre eles, depois `burst_pause_ms` |
| Filtro de janela | Antes de cada ação, `WindowFilter.allows()`; se False, **pula** a ação |
| Proteção da própria janela | Nunca clica sobre uma janela do Clickr nem envia teclas para ela (ver regra 8) |
| Delay de início | Aguarda `start_delay_ms` antes do primeiro tick (fase `countdown`) |
| Limite de cliques | Para ao atingir `max_clicks` (se definido) |
| Duração máxima | Para ao atingir `max_duration_ms` desde o fim do delay (se definido) |
| Start/stop | Botão pulse na UI, atalho global, item Iniciar/Parar da bandeja, agenda |
| Contador | Incrementa a cada ação (duplo conta 2; hold conta 1 no press; ação pulada não conta) |

## Regras

1. O loop roda em **thread dedicada**; a UI apenas observa estado (enviado pelo backend com limite de frequência).
2. Parada: UI, atalho, bandeja, limite N, duração máxima; hold libera o botão/teclas ao parar.
3. Erros do backend de input (`OSError` / `ValueError`) são expostos em `last_error` e interrompem o loop — sem retry silencioso.
4. Alterar configuração com o motor ativo aplica no próximo tick (sem reset obrigatório do contador).
5. Em hold, após o press inicial o loop só observa stop/duração (não re-clica).
6. Ação pulada (filtro ou proteção da própria janela) **não** avança a sequência e fica registrada em `blocked` (`filter` / `own_window`).
7. Cada espera mira um **instante agendado** (deadline): o tempo gasto na própria ação não se soma ao intervalo. Se o atraso passar de 20 ms, o agendamento é ressincronizado a partir de "agora" em vez de disparar cliques em sequência para compensar.
8. Proteção da própria janela:
   - Clique: no Windows, bloqueia se o ponto-alvo (ou o cursor, no modo cursor) estiver sobre qualquer janela do processo do Clickr; em macOS/Linux, se estiver dentro do retângulo da janela principal visível.
   - Tecla: no Windows, bloqueia enquanto a janela em foco for do Clickr; em macOS/Linux essa consulta não existe e a tecla não é bloqueada.
9. Coordenadas absolutas no Windows usam `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK` (multi-monitor).
10. No Windows, a resolução do timer do sistema é elevada para 1 ms enquanto o motor roda.

## Estado exposto

`running`, `click_count`, `started_at`, `last_error`, `phase`, `starts_at`, `elapsed_ms`, `actual_cps`, `sequence_index`, `blocked` — ver [`feedback-execucao`](../feedback-execucao/regras-de-negocio.md).

## Fora do escopo desta feature

Macro, scheduler, script DSL, compact mode (Tier 3).
