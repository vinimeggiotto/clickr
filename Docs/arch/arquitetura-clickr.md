# Arquitetura — Clickr

## Visão geral

Clickr é um autoclicker desktop **multiplataforma** (Windows, macOS, Linux) com UI HTML (concept amber) embutida via **pywebview**. O motor de cliques roda em Python nativo: no Windows usa `ctypes` + Win32 `SendInput`; em macOS/Linux usa `pynput`.

## Camadas

| Pasta | Papel |
|-------|--------|
| `ui/` | Device Clickr + overlay + catálogos `locales/`; consome `window.pywebview.api` |
| `app/` | Bootstrap, `AppController`, `SystemTray`, `AppSettings`, `paths` |
| `core/` | `ClickEngine`, fachada `sendinput` (+ backends), DPI awareness |
| `hotkeys/` | Hotkey global configurável via `pynput` |
| `profiles/` | Persistência + import/export JSON em `user_data_dir()/profiles/` |
| `window_filter/` | Regra de foco por processo/título (Win32 / osascript / xprop) |
| `sequence/` | `SequenceRunner` multi-ponto |
| `assets/` | Ícone da bandeja |
| `macros/` | `MacroRecorder` / `MacroPlayer` (pynput → fachada sendinput) |
| `scheduler/` | Agendamento de início (datetime local) |
| `scripts/` | DSL `click` / `move` / `wait` / `key` / `loop` |
| `packaging/` | Specs PyInstaller por SO |
| `app/paths.py` | Recursos (dev / `_MEIPASS`) e `user_data_dir()` multi-SO |

## Fluxo

1. `main.py` → `enable_dpi_awareness()` (no-op fora do Windows) → `app.bootstrap.run()`
2. pywebview carrega `ui/index.html` com `js_api=AppController` (UI via `app.paths.ui_dir`)
3. UI chama bridge: motor, pick, sequência, perfis, macro, script, agenda, compact mode, settings/locale
4. `ClickEngine` aplica jitter, burst, sequência; consulta `WindowFilter.allows()` antes de cada clique
5. Macro/script usam a fachada de input em threads próprias; scheduler dispara `engine.start()` no horário
6. Hotkey global: para macro/script se ativos; senão alterna o motor
7. Fechar a janela oculta na bandeja; **Sair** encerra o processo

## Paths de dados do usuário

| SO | Diretório |
|----|-----------|
| Windows | `%APPDATA%/Clickr` |
| macOS | `~/Library/Application Support/Clickr` |
| Linux | `$XDG_CONFIG_HOME/Clickr` ou `~/.config/Clickr` |

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
- Windows: clique absoluto com `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK`.
- macOS/Linux: move/click/key via pynput; X1/X2 podem ser limitados.
- Filtro de janela: skip do clique quando não permite — não é fallback de negócio.
- Linux sem `xprop` (filtro ligado com critérios): `OSError` explícito — não “libera” o clique.
- Pick location: overlay na tela virtual (multi-monitor quando o backend expõe); XY via cursor.
- Sem fallbacks, retry ou circuit-breaker.
- Janelas elevadas (admin) no Windows podem ignorar input se o Clickr não estiver elevado — documentado, sem relaunch automático.

## Empacote e CI

| SO | Script | Spec | Artefato |
|----|--------|------|----------|
| Windows | `build_exe.ps1` | `packaging/Clickr.windows.spec` | `dist/Clickr.exe` |
| macOS | `build_macos.sh` | `packaging/Clickr.macos.spec` | `dist/Clickr.app` |
| Linux | `build_linux.sh` | `packaging/Clickr.linux.spec` | `dist/Clickr` |

GitHub Actions (`.github/workflows/build.yml`): matrix `windows-latest` / `macos-latest` / `ubuntu-latest`. Em tag `v*`, anexa artefatos à Release.

PyInstaller **não cross-compila**: cada runner gera o binário da própria plataforma.

## Limitações multiplataforma (documentadas)

- **macOS:** autorização de Acessibilidade; Gatekeeper pode exigir “Abrir mesmo assim” (sem notarização nesta entrega).
- **Linux:** suporte inicial focado em **X11**; Wayland restringe input sintético.
- **XBUTTON1/2:** fidelidade plena no Windows; em macOS/Linux depende do backend pynput.

## Dependências

`pywebview`, `pynput`, `pystray`, `Pillow`, `pyinstaller` (empacote).
