# DOC — app/controller.py

## Objetivo

Expor a API JS do pywebview e orquestrar motor, hotkeys, perfis, tray, pick, sequência, macros, scheduler e scripts.

## Dependências

- `core.engine.ClickEngine`, `core.sendinput`
- `hotkeys.HotkeyService`, `profiles.ProfilesRepo`, `app.tray.SystemTray`
- `app.settings.AppSettings`
- `macros.MacroRecorder`, `macros.MacroPlayer`
- `scheduler.Scheduler`, `scripts.ScriptRunner`
- `app.paths.ui_dir`, `webview`

## Lógica central

- `set_config` mescla parcial; sync de hotkey / always-on-top; `compact_mode` via config.
- Exclusão mútua: start do motor para macro/script; play/run param o motor.
- Hotkey: ignora durante gravação de macro/hotkey/pick; para macro/script se ativos; senão toggle do motor.
- Scheduler dispara `_on_schedule_fire` → `engine.start()`.
- Fechar janela → hide (tray); quit do tray encerra.
- `_ui_alive` + `_clear_ui_callbacks()` no `shutdown`: evita `evaluate_js` após WebView2 descartado.

## Assinaturas (bridge)

| Método | Papel |
|--------|--------|
| `start` / `stop` / `get_state` / `set_config` | runtime |
| `set_compact_mode` | UI compacta |
| `pick_location` / `confirm_pick` / `cancel_pick` | captura XY |
| `add_sequence_point` / `remove_sequence_point` / `clear_sequence` | sequência |
| `record_hotkey` / `cancel_record_hotkey` | hotkey |
| `macro_record_start` / `macro_record_stop` / `macro_play` / `macro_stop` / `macro_clear` | macro |
| `schedule_set` / `schedule_cancel` | agenda |
| `script_run` / `script_stop` | script |
| `save_profile` / `load_profile` / `export_profile` / `import_profile` | perfis |
| `set_always_on_top` / `show_window` / `hide_window(notify=False)` | janela; `notify` dispara toast da bandeja |
| `window_minimize` / `window_close` | title bar; close = hide + notify |
| `show_info_popup` / `get_info_popup` / `close_info_popup` | janela auxiliar de ajuda (Assistente) |
| `get_settings` / `set_locale` | preferências do app (`locale`); `set_locale` atualiza menu da bandeja |
