# Feature: Scheduler (agenda)

## Objetivo

Agendar, em data/hora **local**, o início do autoclique, de um perfil, da macro carregada ou do script — uma vez ou de forma recorrente.

## Opções

| Opção | Valores | Papel |
|-------|---------|--------|
| `when` | ISO naive (`YYYY-MM-DDTHH:MM` ou com segundos) | primeiro disparo, horário local |
| `repeat` | `once` (padrão) \| `daily` \| `interval` | repetição |
| `interval_s` | 5 s a 7 dias | usado só com `repeat = interval` |
| `target` | `engine` (padrão) \| `profile` \| `macro` \| `script` | o que iniciar |
| `profile` | nome de perfil salvo | obrigatório com `target = profile` |

## Comportamento

1. `once` e `interval`: o horário deve estar **no futuro**; caso contrário, erro `schedule.past`. `daily` com horário já passado vale a partir da próxima ocorrência desse horário.
2. No disparo: limpa erros, para macro/script em andamento e:
   - `engine`: inicia o motor com a configuração atual;
   - `profile`: para o motor, carrega o perfil e inicia o motor;
   - `macro`: para o motor e reproduz a macro em memória com as repetições/velocidade salvas;
   - `script`: para o motor e executa o último script salvo (`last_script`).
3. Após o disparo: `once` é removido; `daily` avança para o mesmo horário do dia seguinte; `interval` avança `interval_s` a partir do disparo.
4. **Cancelar** remove o agendamento.
5. Apenas um agendamento ativo por vez (novo `schedule_set` substitui o anterior).
6. Sem retry: se o disparo falhar, o erro fica em `Scheduler.last_error` e aparece no estado.
7. **Persistência:** o agendamento ativo é gravado em `settings.json` (`schedule`) e restaurado ao abrir o app. Na restauração, um `once` já vencido é descartado; os recorrentes avançam para a próxima ocorrência.
8. Uma thread confere o relógio de parede a cada segundo (não é um timer único): o disparo continua correto depois de suspender/retomar o computador ou de ajustar o relógio.
9. Renomear um perfil que é alvo do agendamento atualiza o agendamento.
10. Iniciar/parar manualmente o motor não cancela o agendamento.

## Códigos de erro

`schedule.empty`, `schedule.invalid`, `schedule.past`, `schedule.badInterval`, `schedule.needProfile`, `profile.notFound`.

## Bridge

| Método | Papel |
|--------|--------|
| `schedule_set(when, options?)` | agenda (`options`: `repeat`, `interval_s`, `target`, `profile`) |
| `schedule_cancel()` | cancela |

Estado em `get_state().schedule`: `active`, `at` (ISO ou null), `repeat`, `interval_s`, `target`, `profile`.

## UI

Aba **Agenda** (oculta no modo compacto): `datetime-local`, repetição (UMA VEZ / DIÁRIO / A CADA + valor em s/min/h), seletor "O que iniciar" (autoclique, perfil salvo, macro carregada, script) e lista de perfis quando o alvo é perfil. A dica mostra o próximo disparo, o alvo e a repetição.
