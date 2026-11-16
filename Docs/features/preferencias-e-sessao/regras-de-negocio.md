# Feature: Preferências do aplicativo e restauração de sessão

## Objetivo

Separar o que pertence ao **aplicativo** (atalhos, janela, opções de sistema) do que pertence a um **perfil de clique**, e reabrir o Clickr como ele estava na última vez.

## Armazenamento

- Arquivo: `{user_data_dir()}/settings.json`
- Gravação atômica (arquivo temporário no mesmo diretório + troca), para não corromper o arquivo se o app for encerrado no meio da escrita.
- Alterações frequentes (última configuração, texto do script, posição da janela) são agrupadas: a escrita acontece cerca de 0,5 s depois da primeira mudança. As demais são gravadas na hora. Ao encerrar, o que estiver pendente é gravado.

## Chaves

| Chave | Padrão | Papel |
|-------|--------|--------|
| `locale` | `null` | Idioma da UI (ver [`i18n`](../i18n/regras-de-negocio.md)) |
| `hotkeys` | `toggle: "F6"`, demais vazios | Atalho por ação (`toggle`, `stop_all`, `pick_point`, `macro_record`) |
| `activation` | `"toggle"` | Modo do atalho de iniciar/parar: `toggle` ou `hold` |
| `always_on_top` | `true` | Janela sempre no topo |
| `compact_mode` | `false` | Modo compacto |
| `last_config` | `null` | Última configuração de clique usada |
| `last_script` | `""` | Último texto do editor de script (até 100 000 caracteres) |
| `window_pos` | `null` | Última posição `[x, y]` da janela principal |
| `manual_seen` | `false` | Manual/Assistente já concluído |
| `tray_hint_shown` | `false` | Aviso "continua na bandeja" já exibido |
| `time_units` | `ms` para os três campos | Unidade exibida em `start_delay`, `max_duration`, `burst_pause` (`ms`, `s`, `min`, `h`) |
| `launch_at_login` | `false` | Iniciar com o sistema |
| `check_updates` | `false` | Avisar quando houver versão nova |
| `schedule` | `null` | Agendamento ativo |
| `macro` | `repeat: 1`, `speed: 1.0`, `name: ""` | Opções de reprodução e nome da última macro |

## Comportamento

1. **Compatibilidade:** arquivos antigos (só `locale`) continuam válidos — chaves ausentes assumem o padrão. Valores de tipo ou conteúdo inválido voltam ao padrão. Chaves desconhecidas são preservadas ao gravar. Arquivo ilegível → padrões (e aviso no log).
2. **Restauração de sessão** ao abrir:
   - a última configuração de clique (`last_config`) é aplicada ao motor; se for inválida, usa os padrões;
   - atalhos, modo de ativação, sempre no topo, modo compacto e unidades de tempo voltam como estavam;
   - o texto do script e as opções/nome da macro são repostos na UI;
   - a janela reabre na última posição, desde que ainda caia dentro da área de tela atual;
   - o agendamento salvo é reativado (ver [`scheduler`](../scheduler/regras-de-negocio.md));
   - os eventos da macro **não** são restaurados automaticamente (é preciso carregar a macro salva).
3. Toda alteração de configuração de clique (UI, perfil, captura de ponto, atalho) atualiza `last_config`.
4. **Unidades de tempo:** são só apresentação. O backend trabalha sempre em ms; a UI converte ao exibir e ao enviar (aceita vírgula ou ponto decimal).
5. Preferências **não** fazem parte dos perfis v2. Perfis da 1.0.x ainda podem alterar atalho de iniciar/parar, sempre no topo e modo compacto ao serem carregados (ver [`perfis`](../perfis/regras-de-negocio.md)).

## Bridge

| Método | Papel |
|--------|--------|
| `get_settings()` | preferências públicas + `locale`, `supported_locales`, `version`, `profiles`, `macros`, `manual_seen`, `tray_hint_shown`, `last_script` |
| `set_preferences(values)` | altera `always_on_top`, `compact_mode`, `check_updates`, `launch_at_login`, `time_units` (patch parcial), `activation` |
| `set_always_on_top(enabled)` / `set_compact_mode(enabled)` | atalhos para as respectivas preferências |
| `set_locale(code)` | idioma |
| `save_script(source)` | guarda o texto do script |
| `set_manual_seen(seen=True)` | marca o manual como visto |

`get_state().settings` traz: `hotkeys`, `activation`, `always_on_top`, `compact_mode`, `time_units`, `launch_at_login`, `check_updates`.

## Regras

- `activation` fora de `toggle`/`hold` é ignorado.
- Falha ao gravar o arquivo é registrada no log; o app continua com os valores em memória.
- `set_config` com `hotkey` / `always_on_top` / `compact_mode` (chaves legadas) encaminha esses valores às preferências.

## UI

Aba **Run**: toggles Sempre no topo, Modo compacto, Iniciar com o sistema, Avisar quando houver versão nova; seletores de unidade nos campos de delay e duração (e na pausa de burst, aba Adv). Aba **Atalhos**: atalhos e modo de ativação.
