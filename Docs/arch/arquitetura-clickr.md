# Arquitetura — Clickr

## Visão geral

Clickr é um autoclicker desktop **Windows** com UI HTML (concept amber) embutida via **pywebview**. O motor de cliques roda em Python nativo (`ctypes` + Win32 `SendInput`), separado da UI.

## Camadas

| Pasta | Papel |
|-------|--------|
| `ui/` | Device Clickr + overlay + catálogos `locales/`; consome `window.pywebview.api` |
| `app/` | Bootstrap, `AppController`, `SystemTray`, `AppSettings` |
| `core/` | `ClickEngine`, `sendinput`, DPI awareness |
| `hotkeys/` | Hotkey global configurável via `pynput` |
| `profiles/` | Persistência + import/export JSON em `%APPDATA%/Clickr/profiles/` |
| `window_filter/` | Regra de foco por processo/título |
| `sequence/` | `SequenceRunner` multi-ponto |
| `assets/` | Ícone da bandeja |
| `macros/` | `MacroRecorder` / `MacroPlayer` (pynput → SendInput) |
| `scheduler/` | Agendamento de início (datetime local) |
| `scripts/` | DSL `click` / `move` / `wait` / `key` / `loop` |
| `app/paths.py` | Recursos em dev e `sys._MEIPASS` (frozen) |

## Fluxo (Tier 1–3)

1. `main.py` → `enable_dpi_awareness()` → `app.bootstrap.run()`
2. pywebview carrega `ui/index.html` com `js_api=AppController` (UI via `app.paths.ui_dir`)
3. UI chama bridge: motor, pick, sequência, perfis, macro, script, agenda, compact mode, settings/locale
4. `ClickEngine` aplica jitter, burst, sequência; consulta `WindowFilter.allows()` antes de cada clique
5. Macro/script usam SendInput em threads próprias; scheduler dispara `engine.start()` no horário
6. Hotkey global: para macro/script se ativos; senão alterna o motor
7. Fechar a janela oculta na bandeja; **Sair** encerra o processo

## Contrato de configuração (núcleo + Tier 1–3)

```json
{
  "interval_ms": 80,
  "jitter_ms": 0,
  "button": "left",
  "click_type": "single",
  "position_mode": "cursor",
  "fixed_x": 0,
  "fixed_y": 0,
  "hold": false,
  "start_delay_ms": 0,
  "max_clicks": null,
  "max_duration_ms": null,
  "burst_count": null,
  "burst_pause_ms": null,
  "sequence": [],
  "window_filter": { "enabled": false, "process": "", "title_contains": "" },
  "hotkey": "F6",
  "always_on_top": true,
  "compact_mode": false
}
```

`button`: `left` | `right` | `middle` | `x1` | `x2`.

Estado runtime: `running`, `click_count`, `started_at`, `last_error`, `picking`, `recording_hotkey`, `profiles`, `macro`, `schedule`, `script`.

## Decisões

- Timer no **Python** (`time.perf_counter`), não no `setInterval` do JS.
- Clique absoluto: `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK`.
- Filtro de janela: skip do clique quando não permite — não é fallback de negócio.
- Pick location: overlay na tela virtual (multi-monitor); XY via `GetCursorPos`.
- Sem fallbacks, retry ou circuit-breaker.
- Janelas elevadas (admin) podem ignorar input se o Clickr não estiver elevado — documentado, sem relaunch automático.

## Dependências

`pywebview`, `pynput`, `pystray`, `Pillow`, `pyinstaller` (empacote → `Clickr.spec` / `build_exe.ps1`).
