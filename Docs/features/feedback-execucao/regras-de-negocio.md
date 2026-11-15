# Feature: Feedback de execução

## Objetivo

Mostrar, em tempo real, em que fase o motor está, quanto falta para começar, há quanto tempo roda, a taxa real de ações e por que uma ação foi pulada.

## Campos do estado

| Campo | Tipo | Significado |
|-------|------|-------------|
| `phase` | `idle` \| `countdown` \| `running` | Parado, aguardando o delay inicial ou executando |
| `starts_at` | epoch (s) ou `null` | Instante em que o delay inicial termina; só em `countdown` |
| `elapsed_ms` | int | Tempo de execução contado a partir do **fim** do delay inicial; congelado ao parar (fica visível até o próximo início) |
| `actual_cps` | float (1 casa) | Ações contabilizadas no último segundo; 0 fora de `running` |
| `sequence_index` | int ou `null` | Passo da sequência do próximo clique; `null` sem sequência ou na ação de teclado |
| `blocked` | `"filter"` \| `"own_window"` \| `null` | Motivo de a última ação ter sido pulada; `null` quando a última ação foi executada ou fora de `running` |
| `engine_running` | bool | Só o motor de clique |
| `running` | bool | Motor **ou** macro em reprodução **ou** script |

Demais campos de contexto: `click_count`, `started_at`, `script.line`, `macro.iteration`, `window_capture`.

## Comportamento

1. Com `start_delay_ms > 0`, o motor entra em `countdown`; ao fim do delay passa a `running` e o tempo decorrido começa a contar.
2. Parar durante a contagem não executa nenhuma ação e deixa `elapsed_ms = 0`.
3. A taxa real considera cliques efetivos (duplo conta 2); ações puladas não entram.
4. `blocked = "filter"`: a janela em foco não casa com o filtro. `blocked = "own_window"`: o alvo é a janela do próprio Clickr.
5. **Entrega à UI:** threads de trabalho (motor, macro, script, agenda, atalhos) apenas sinalizam; uma thread dedicada envia o estado completo à UI no máximo ~15 vezes por segundo. A UI mantém, além disso, uma consulta periódica a `get_state`.
6. Contagem regressiva e relógio são interpolados na UI a cada 100 ms entre duas atualizações.
7. **Erros:** `last_error` é um único objeto `{ code, message, params }` (ou `null`), escolhido nesta ordem: ação da UI, motor, macro, script, agenda. Cada chamada da bridge limpa os erros anteriores.

## UI

- Botão pulse: durante a contagem mostra os segundos restantes (com uma casa decimal abaixo de 10 s).
- Sob o contador: tempo decorrido (`mm:ss` ou `h:mm:ss`) e taxa real ("/s real").
- Linha de status: `aguardando` (contagem), `alvo sobre o Clickr` (`own_window`), `fora da janela do filtro` (`filter`), além de parado / ativo / gravando / macro / script.
- Aba Point: o passo atual da sequência fica destacado enquanto o motor roda.
- Aba Script: linha em execução. Aba Macro: rodada atual quando há repetições.
- Bandeja: ícone com ponto verde e item "Parar" enquanto algo está em execução.
