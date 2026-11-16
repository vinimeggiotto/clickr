# Arquitetura — Clickr

## Visão geral

Clickr é um autoclicker desktop **multiplataforma** (Windows, macOS, Linux) com UI HTML (concept amber) embutida via **pywebview**. O motor de cliques roda em Python nativo: no Windows usa `ctypes` + Win32 `SendInput`; em macOS/Linux usa `pynput`.

## Camadas

| Pasta | Papel |
|-------|--------|
| `ui/` | Device Clickr + overlay + catálogos `locales/`; consome `window.pywebview.api` |
| `app/` | Bootstrap, `AppController` (bridge + decorador `@api`), `SystemTray`, `AppSettings`, `paths` e os módulos de apoio abaixo |
| `core/` | `ClickEngine`, fachada `sendinput` (+ backends win32 / pynput / nulo), tabela de teclas, erros com código, DPI awareness |
| `hotkeys/` | Atalhos globais por ação, com combinações (`RegisterHotKey` no Windows; `pynput` nos demais e como reserva) |
| `profiles/` | Persistência (formato v2, leitura de v1) + renomear/excluir/import/export JSON em `user_data_dir()/profiles/` |
| `window_filter/` | Regra de foco por processo/título (Win32 / osascript / xprop) + detecção da janela do próprio Clickr |
| `sequence/` | `SequenceRunner` multi-ponto |
| `assets/` | Ícone da bandeja |
| `macros/` | `MacroRecorder` / `MacroPlayer` (pynput → fachada sendinput) / `MacrosRepo` (`user_data_dir()/macros/`) |
| `scheduler/` | Agendamento único ou recorrente (datetime local, relógio de parede) |
| `scripts/` | DSL `click` / `dclick` / `move` / `drag` / `scroll` / `wait` / `key` / `type` / `loop` |
| `tests/` | Suíte pytest (backend de input nulo) e teste de UI ponta a ponta (`tests/ui/`) |
| `packaging/` | Specs PyInstaller por SO |
| `VERSION` | Semver do app (fonte da verdade; embutido no bundle) |
| `app/paths.py` | Recursos (dev / `_MEIPASS`), `app_version()`, `user_data_dir()` multi-SO |

## Mapa de módulos

| Módulo | Papel |
|--------|--------|
| `main.py` | Entrypoint: log, DPI awareness, flag `--minimized`, `app.bootstrap.run()` |
| `app/bootstrap.py` | Instância única, criação da janela, ciclo de vida |
| `app/controller.py` | `AppController`: API JS, estado, orquestração, tratamento de erros (`@api`) |
| `app/settings.py` | Preferências do app em `settings.json` (escrita atômica e agrupada) |
| `app/notifier.py` | `UiNotifier`: push de estado para a UI com limite de frequência |
| `app/single_instance.py` | Trava de instância única + pedido de "mostrar janela" |
| `app/tray.py` | Bandeja (Iniciar/Parar, Mostrar, Ocultar, Sair; ícone ativo) |
| `app/autostart.py` | Iniciar com o sistema (Registro / LaunchAgent / `.desktop`) |
| `app/updates.py` | Verificação opcional de release mais nova no GitHub |
| `app/log.py` | Log rotativo em `clickr.log` |
| `app/fsutil.py` | Gravação atômica de texto/JSON |
| `app/paths.py` | Recursos (dev / `_MEIPASS`), `app_version()`, `user_data_dir()` |
| `core/engine.py` | Loop de autoclique (mouse/teclado), fases, guards, estatísticas |
| `core/types.py` | `ClickConfig`, `RuntimeState`, constantes de versão de perfil |
| `core/keys.py` | Tabela nome ↔ VK, modificadores, `parse_key_sequence` |
| `core/errors.py` | `ClickrError` e formato `{code, message, params}` |
| `core/sendinput.py` | Fachada; escolhe `sendinput_win32` / `sendinput_pynput` / `sendinput_null` |
| `core/dpi.py` | DPI awareness per-monitor (Windows) |
| `hotkeys/service.py` | `HotkeyService`: atalho por ação, despacho, captura |
| `hotkeys/combo.py` | `Combo` e `parse_combo` |
| `hotkeys/backend_win32.py` / `backend_pynput.py` | Backends de detecção |
| `hotkeys/keynames.py` | Nome estável de teclas pynput |
| `macros/recorder.py` / `player.py` / `repo.py` | Gravar, reproduzir, salvar macros |
| `profiles/repo.py` | Repositório de perfis |
| `scheduler/service.py` | Agenda |
| `scripts/runner.py` | Parser e executor da DSL |
| `sequence/runner.py` | Índice cíclico da sequência |
| `window_filter/filter.py` | Filtro de janela e detecção de janela própria |

## Fluxo

1. `main.py` → `setup_logging()` → `enable_dpi_awareness()` (no-op fora do Windows; falha só é registrada) → `app.bootstrap.run(start_minimized)`
2. `SingleInstance.acquire()`: se já existe um Clickr aberto, pede que ele mostre a janela e encerra
3. `AppController()` carrega `settings.json`, restaura a última configuração de clique e os atalhos
4. pywebview carrega `ui/index.html` com `js_api=AppController` (UI via `app.paths.ui_dir`); com `--minimized` a janela nasce oculta
5. Com a GUI no ar, `bootstrap_services()` inicia atalhos, bandeja, guards do motor, `UiNotifier`, restaura o agendamento, reaplica o início automático e (se ligado) consulta atualização
6. UI chama a bridge: motor, pick, sequência, perfis, atalhos, macro, script, agenda, preferências/locale. Métodos `@api` devolvem sempre o estado; erros chegam em `last_error` como `{code, message, params}`
7. `ClickEngine` aplica jitter, burst, sequência; antes de cada ação consulta `WindowFilter.allows()` e os guards (não clica na janela do Clickr nem envia teclas para ela)
8. Motor, macro, script, agenda e atalhos chamam `UiNotifier.signal()`; uma thread envia o estado à UI (`window.__clickrApplyState`) no máximo ~15×/s e atualiza a bandeja
9. Macro/script usam a fachada de input em threads próprias; o scheduler dispara o alvo configurado (motor, perfil, macro ou script) no horário
10. Atalhos globais: iniciar/parar (para macro/script se ativos; senão alterna o motor, ou "segura"), parar tudo, capturar ponto no cursor, gravar/parar macro
11. Fechar a janela oculta na bandeja; **Sair** encerra o processo (grava preferências pendentes e libera a trava)

## Paths de dados do usuário

| SO | Diretório |
|----|-----------|
| Windows | `%APPDATA%/Clickr` |
| macOS | `~/Library/Application Support/Clickr` |
| Linux | `$XDG_CONFIG_HOME/Clickr` ou `~/.config/Clickr` |

Conteúdo do diretório:

| Item | Papel |
|------|--------|
| `settings.json` | Preferências do app e sessão (idioma, atalhos, última config, agendamento…) |
| `profiles/{nome}.json` | Perfis de clique |
| `macros/{nome}.json` | Macros salvas |
| `clickr.log` (+ backups) | Log rotativo |
| `clickr.lock` | Trava de instância única (macOS / Linux) |
| `show.request` | Pedido temporário de "mostrar janela" de uma segunda instância |

## Contrato de configuração de clique (`ClickConfig`)

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
  "restore_cursor": false,
  "position_jitter_px": 0,
  "action": "mouse",
  "key_name": "SPACE"
}
```

`button`: `left` | `right` | `middle` | `x1` | `x2`. `action`: `mouse` | `key`.

`hotkey`, `always_on_top` e `compact_mode` **não** fazem mais parte deste contrato: são preferências do aplicativo.

Perfil em disco (formato v2): `{ "name": "...", "version": 2, "config": { ...ClickConfig } }`. Arquivos da 1.0.x (sem `version`) continuam sendo lidos — ver [`Docs/features/perfis`](../features/perfis/regras-de-negocio.md).

## Preferências do aplicativo (`settings.json`)

`locale`, `hotkeys` (`toggle`, `stop_all`, `pick_point`, `macro_record`), `activation` (`toggle` | `hold`), `always_on_top`, `compact_mode`, `last_config`, `last_script`, `window_pos`, `manual_seen`, `tray_hint_shown`, `time_units`, `launch_at_login`, `check_updates`, `schedule`, `macro` (`repeat`, `speed`, `name`).

## Estado runtime (`get_state()`)

`running`, `engine_running`, `click_count`, `started_at`, `last_error`, `config`, `picking`, `recording_hotkey`, `recording_hotkey_action`, `phase`, `starts_at`, `elapsed_ms`, `actual_cps`, `sequence_index`, `blocked`, `macro`, `schedule`, `script`, `window_capture`, `update`, `settings`.

## Decisões

- Timer no **Python** (`time.perf_counter`), não no `setInterval` do JS; esperas por instante agendado (deadline), sem acumular o tempo da ação.
- Estado empurrado do Python para a UI com limite de frequência; threads de input nunca chamam a UI diretamente.
- Erros de domínio têm código estável (`ClickrError`); a tradução é responsabilidade da UI (`errors.<code>`).
- Preferências do app separadas dos perfis; gravações em disco atômicas.
- Identificador canônico de tecla = código VK do Win32 em todas as plataformas (`core.keys`).
- Atalhos no Windows via `RegisterHotKey` (a tecla não vaza para o programa em foco); pynput nos demais SOs e como reserva.
- Uma única instância por usuário.
- Rede só sob opção explícita do usuário (aviso de versão nova); nenhuma telemetria.
- Windows: clique absoluto com `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK`.
- macOS/Linux: move/click/key via pynput; X1/X2 podem ser limitados.
- Filtro de janela: skip do clique quando não permite — não é fallback de negócio.
- O motor nunca clica sobre a janela do próprio Clickr; no Windows também não envia teclas enquanto ela está em foco.
- Linux sem `xprop` (filtro ligado com critérios): `OSError` explícito — não “libera” o clique.
- Pick location: overlay na tela virtual (multi-monitor quando o backend expõe); XY via cursor.
- Sem retry nem circuit-breaker nas ações de input. Degradações explícitas e registradas no log: sem bandeja, fechar a janela encerra o app; combo recusado pelo `RegisterHotKey` usa o listener pynput; ícone ausente usa um substituto desenhado.
- Janelas elevadas (admin) no Windows podem ignorar input se o Clickr não estiver elevado — documentado, sem relaunch automático.

## Empacote e CI

| SO | Script | Spec | Artefato |
|----|--------|------|----------|
| Windows | `build_exe.ps1` | `packaging/Clickr.windows.spec` | `dist/Clickr.exe` |
| macOS | `build_macos.sh` | `packaging/Clickr.macos.spec` | `dist/Clickr.app` |
| Linux | `build_linux.sh` | `packaging/Clickr.linux.spec` | `dist/Clickr` |

GitHub Actions (`.github/workflows/build.yml`):

- job `test` (`ubuntu-latest`): instala `requirements-dev.txt` e roda `python -m pytest -q` com `CLICKR_INPUT_BACKEND=null`;
- job `build`: matrix `windows-latest` / `macos-latest` / `ubuntu-latest`;
- job `release` (tag `v*`, depende de `test` e `build`): anexa os artefatos à Release junto com o arquivo `SHA256SUMS`.

Os specs usam `upx=False` (binários sem compressão UPX).

## Testes

| Comando | O que cobre |
|---------|-------------|
| `CLICKR_INPUT_BACKEND=null python -m pytest -q` | Suíte `tests/` (motor, tipos, atalhos, macro, perfis, agenda, script, settings, controller, locales) com backend de input nulo e dublês de pywebview/pynput |
| `node tests/ui/smoke.cjs` | Teste de UI ponta a ponta: Chromium (Playwright) contra `tests/ui/devserver.py`, que serve `ui/` e expõe o `AppController` real por HTTP |

PyInstaller **não cross-compila**: cada runner gera o binário da própria plataforma.

## Limitações multiplataforma (documentadas)

- **macOS:** autorização de Acessibilidade; Gatekeeper pode exigir “Abrir mesmo assim” (sem notarização nesta entrega).
- **Linux:** suporte inicial focado em **X11**; Wayland restringe input sintético.
- **XBUTTON1/2:** fidelidade plena no Windows; em macOS/Linux depende do backend pynput.

## Dependências

`pywebview`, `pynput`, `pystray`, `Pillow`, `pyinstaller` (empacote) — com faixas de versão fixadas em `requirements.txt`. Desenvolvimento: `pytest` (`requirements-dev.txt`); o teste de UI usa Node.js + Playwright.
