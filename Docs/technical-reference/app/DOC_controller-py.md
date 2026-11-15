# DOC — app/controller.py

## Objetivo

Expor a API JS do pywebview e orquestrar motor, hotkeys, perfis, preferências, tray, pick, sequência, macros, scheduler, scripts, início automático e verificação de atualização.

## Dependências

- `core.engine.ClickEngine`, `core.sendinput`, `core.errors`, `core.keys.parse_key_sequence`, `core.types`
- `hotkeys.service.HotkeyService`, `profiles.ProfilesRepo`, `app.tray.SystemTray` (import tardio)
- `app.settings.AppSettings`, `app.notifier.UiNotifier`, `app.autostart`, `app.updates`, `app.log`
- `macros.MacroRecorder`, `macros.MacroPlayer`, `macros.MacrosRepo`
- `scheduler.Scheduler`, `scripts.ScriptRunner`
- `window_filter.filter.foreground_is_own_window`, `point_in_own_window`
- `app.paths` (`ui_dir`, `locales_dir`, `app_version`), `webview`

## Lógica central

- **Decorador `@api`:** envolve os métodos de ação da bridge. Limpa erros anteriores (UI, motor, macro, script, agenda), executa e, se houver exceção, registra o erro (`ClickrError` → seu código; outras → `generic`, com log) e **devolve o estado** em vez de propagar a exceção para o JavaScript.
- **Erro único:** `get_state().last_error` é `{code, message, params}` ou `null`, na ordem: ação da UI, motor, macro, script, agenda.
- **Construtor:** carrega `AppSettings`, restaura `last_config` no motor e cria o `HotkeyService` com os atalhos salvos.
- **`bootstrap_services()`:** inicia hotkeys, aplica always-on-top, cria a bandeja, instala `click_guard` / `key_guard` no motor e `ignore_point` no gravador, liga os callbacks ao `UiNotifier.signal`, restaura o agendamento salvo, reaplica o início automático e dispara a verificação de atualização se ligada. Falhas de hotkeys ou bandeja são registradas e não derrubam o app.
- **Push de estado:** `UiNotifier` chama `_push_state`, que serializa `get_state()` e executa `window.__clickrApplyState(...)` via `evaluate_js`; também sincroniza ícone/rótulo da bandeja. `_ui_alive` impede `evaluate_js` após o WebView ser descartado.
- **Config × preferências:** `_apply_config` aplica no motor e grava `last_config` (com atraso). Chaves legadas (`hotkey`, `always_on_top`, `compact_mode`) são encaminhadas a `_apply_prefs` (UI e perfis v1) ou descartadas (perfis v2). `key_name` inválido gera `key.unsupported` e é removido do patch. `_apply_prefs` valida e grava preferências e aplica efeitos (on-top, autostart, update check).
- **`set_config`:** mescla parcial; ao entrar em ponto fixo sem XY captura o cursor; mantém `hold` e `click_type` coerentes; `window_filter` aceita patch parcial.
- **Perfis:** `_load_profile_document` — v2 substitui a config de clique (`replace=True`, sem preferências); v1 mescla sobre a config atual, zera os campos que não existiam na 1.0.x e aplica as preferências legadas. Importação com nome já existente devolve `import_conflict` e guarda a pendência até `import_profile_confirm()`.
- **Exclusão mútua:** start do motor para macro/script; gravar/reproduzir macro e rodar script param o motor. Nenhuma dessas ações cancela o agendamento.
- **Atalhos (`_on_hotkey_action`):** ignorados durante gravação de atalho; `stop_all` para tudo (inclusive fecha o overlay); com overlay aberto os demais são ignorados; `toggle` para macro/script ou alterna o motor (ou `_start_while_held` no modo segurar, com thread que observa a tecla); `pick_point` grava o cursor como ponto fixo; `macro_record` alterna a gravação removendo as teclas do próprio atalho.
- **Guards:** `_click_guard` usa `point_in_own_window` (Windows) ou o retângulo da janela principal visível; `_key_guard` usa `foreground_is_own_window`.
- **Captura de janela:** `capture_foreground_window` agenda um `Timer`; ao disparar, preenche `window_filter` ou registra `filter.*`.
- **Agenda (`_on_schedule_fire`):** executa o alvo (`engine` / `profile` / `macro` / `script`) e regrava `schedule` em `settings.json`.
- **Janela:** posição salva em `window_pos` no evento `moved`; fechar → hide (se houver bandeja); quit do tray encerra; `shutdown()` para tudo, grava preferências pendentes e mantém o agendamento salvo.

## Assinaturas (bridge)

Métodos marcados com ● usam `@api` (devolvem o estado; erros em `last_error`).

| Método | Papel |
|--------|--------|
| ● `start` / ● `stop` / `get_state` / ● `set_config(config)` | runtime |
| ● `set_preferences(values)` / ● `set_compact_mode(enabled)` / ● `set_always_on_top(enabled)` | preferências do app |
| `get_settings` / `set_locale(code)` | preferências + `version`, `profiles`, `macros`, `manual_seen`, `tray_hint_shown`, `last_script`; `set_locale` atualiza a bandeja |
| `save_script(source)` / `set_manual_seen(seen=True)` | sessão |
| ● `pick_location(target="fixed", delay_ms=0)` / ● `confirm_pick` / ● `cancel_pick` | captura XY (ponto fixo ou sequência) |
| ● `add_sequence_point` / ● `update_sequence_point(index, patch)` / ● `move_sequence_point(index, to)` / ● `remove_sequence_point(index)` / ● `clear_sequence` | sequência |
| ● `capture_foreground_window(delay_s=3.0)` / ● `cancel_capture_foreground_window` | "usar janela atual" do filtro |
| ● `record_hotkey(action="toggle")` / ● `cancel_record_hotkey` / ● `set_hotkey(action, combo)` / ● `clear_hotkey(action)` | atalhos por ação |
| ● `capture_action_key` | captura a tecla do autoclique de teclado |
| ● `macro_record_start` / ● `macro_record_stop` / ● `macro_play(repeat?, speed?)` / ● `macro_stop` / ● `macro_clear` / ● `macro_set_options(repeat?, speed?)` | macro |
| ● `macro_save(name)` / ● `macro_load(name)` / ● `macro_delete(name)` / `list_macros` | macros salvas |
| ● `schedule_set(when, options?)` / ● `schedule_cancel` | agenda |
| ● `script_run(source)` / ● `script_stop` | script |
| ● `save_profile` / ● `load_profile` / ● `rename_profile(old, new)` / ● `delete_profile` / ● `export_profile` / ● `import_profile` / ● `import_profile_confirm` / `list_profiles` | perfis |
| ● `check_updates_now` / `open_update_page` | atualização |
| `show_window` / `hide_window(notify=False)` | janela; `notify` mostra o aviso da bandeja (só na primeira vez) |
| `window_minimize` / `window_close` | title bar; close = hide + aviso, ou encerra se não há bandeja |
| `show_info_popup` / `get_info_popup` / `close_info_popup` | janela auxiliar de ajuda (Assistente) |

Campos extras devolvidos por algumas ações: `saved_profile`, `renamed_profile`, `deleted_profile`, `imported_profile`, `import_conflict`, `exported_path`, `profiles`, `saved_macro`, `macros`.

## Assinaturas (estado — `get_state()`)

`running`, `engine_running`, `click_count`, `started_at`, `last_error`, `config`, `picking`, `recording_hotkey`, `recording_hotkey_action`, `phase`, `starts_at`, `elapsed_ms`, `actual_cps`, `sequence_index`, `blocked`, `macro` (`recording`, `playing`, `event_count`, `duration_ms`, `iteration`, `repeat`, `speed`, `name`), `schedule` (`active`, `at`, `repeat`, `interval_s`, `target`, `profile`), `script` (`running`, `line`), `window_capture` (`active`, `ends_at`), `update` (`{version, url}` ou `null`), `settings` (`hotkeys`, `activation`, `always_on_top`, `compact_mode`, `time_units`, `launch_at_login`, `check_updates`).

## Assinaturas (ciclo de vida — usadas por `app.bootstrap`)

| Método | Papel |
|--------|--------|
| `attach_window(window)` | guarda a janela e observa o evento `moved` |
| `initial_window_pos()` | última posição salva, se ainda visível na tela virtual |
| `bootstrap_services()` | inicia serviços após a GUI subir |
| `start_tray(detached=False)` | cria a bandeja (idempotente) |
| `has_tray()` / `mark_window_hidden()` / `should_close_to_tray()` | apoio ao fechamento e ao início minimizado |
| `shutdown()` | encerra serviços e grava pendências |
