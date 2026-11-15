"""AppController — ponte entre UI (pywebview JS API), motor, hotkeys, perfis e tray."""

from __future__ import annotations

import functools
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import webview

from app import autostart, updates
from app.log import get_logger
from app.notifier import UiNotifier
from app.paths import app_version, locales_dir, ui_dir
from app.settings import ACTIVATION_MODES, HOTKEY_ACTIONS, SUPPORTED_LOCALES, AppSettings
from core import sendinput
from core.engine import ClickEngine
from core.errors import ClickrError, error_from_exception, normalize_error
from core.keys import parse_key_sequence
from core.types import LEGACY_APP_KEYS, PROFILE_VERSION, V1_CONFIG_KEYS, ClickConfig
from hotkeys.service import HotkeyService
from macros.player import MacroPlayer
from macros.recorder import MacroRecorder
from macros.repo import MacrosRepo
from profiles.repo import ProfilesRepo
from scheduler.service import Scheduler
from scripts.runner import ScriptRunner
from window_filter.filter import foreground_is_own_window, point_in_own_window

UI_DIR = ui_dir()
log = get_logger()


def api(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Envolve um método da bridge JS: limpa erros anteriores, executa e, em caso
    de exceção, registra o erro (com código traduzível) e devolve o estado em
    vez de propagar a exceção para o JavaScript.
    """

    @functools.wraps(fn)
    def wrapper(self: "AppController", *args: Any, **kwargs: Any) -> Any:
        self._clear_errors()
        try:
            return fn(self, *args, **kwargs)
        except ClickrError as exc:
            self._error = exc.to_dict()
        except Exception as exc:  # noqa: BLE001 - fronteira da bridge
            log.exception("Falha em %s", fn.__name__)
            self._error = error_from_exception(exc)
        return self.get_state()

    return wrapper


class AppController:
    """
    Expõe a API JS do pywebview e orquestra ClickEngine, HotkeyService,
    ProfilesRepo, SystemTray, macros, scheduler e scripts.
    """

    def __init__(self) -> None:
        self._engine = ClickEngine()
        self._profiles = ProfilesRepo()
        self._macros = MacrosRepo()
        self._settings = AppSettings()
        self._restore_last_config()
        self._hotkeys = HotkeyService(
            on_action=self._on_hotkey_action,
            bindings=self._settings.get("hotkeys"),
        )
        self._macro_recorder = MacroRecorder()
        self._restore_last_macro()
        self._macro_player = MacroPlayer()
        self._scheduler = Scheduler()
        self._script = ScriptRunner()
        self._window: Any = None
        self._overlay: Any = None
        self._info: Any = None
        self._info_payload: dict[str, str] = {"title": "", "body_html": ""}
        self._tray: Any = None
        self._error: Optional[dict[str, Any]] = None
        self._window_visible = True
        self._notifier = UiNotifier(self._push_state)
        self._picking = False
        self._recording_hotkey = False
        self._recording_hotkey_action = ""
        self._hold_watch: Any = None
        self._pending_import: Optional[tuple[Path, str]] = None
        self._update_info: Optional[dict[str, str]] = None
        self._update_checking = False
        self._tray_running: Optional[bool] = None
        self._pick_target = "fixed"
        self._pick_delay_ms = 0
        self._wf_capture_until: Optional[float] = None
        self._wf_capture_timer: Optional[threading.Timer] = None
        self._quit_requested = False
        self._ui_alive = False

    def attach_window(self, window: Any) -> None:
        self._window = window
        try:
            window.events.moved += self._on_window_moved
        except Exception:
            log.info("Evento de movimento da janela indisponível")
        try:
            # Reaplica quando a janela já existe de fato (a primeira tentativa
            # pode acontecer antes de o formulário nativo estar pronto).
            window.events.shown += lambda *_a: self._apply_always_on_top(
                bool(self._settings.get("always_on_top"))
            )
        except Exception:
            log.info("Evento de exibição da janela indisponível")

    @staticmethod
    def _legacy_win_scale() -> float:
        """
        Fator de escala que o pywebview < 6 aplica no Windows às coordenadas
        passadas a create_window (ele devolve posições em pixels físicos, mas
        multiplica x/y pela escala do monitor ao criar a janela). 1.0 nos demais.
        """
        if sys.platform != "win32":
            return 1.0
        try:
            from importlib.metadata import version

            if int(version("pywebview").split(".")[0]) >= 6:
                return 1.0
            import ctypes

            scale = ctypes.WinDLL("shcore").GetScaleFactorForDevice(0) / 100.0
            return scale if scale > 0 else 1.0
        except Exception:
            return 1.0

    def to_create_coords(self, x: int, y: int) -> tuple[int, int]:
        """Converte uma posição de tela para o que create_window espera receber."""
        scale = self._legacy_win_scale()
        return int(round(x / scale)), int(round(y / scale))

    def _transparent_overlay_supported(self) -> bool:
        """No Windows com pywebview < 6 a transparência usa chave de cor e
        tingiria o overlay; lá ele continua opaco como na 1.0."""
        return not (sys.platform == "win32" and self._pywebview_major() < 6)

    @staticmethod
    def _pywebview_major() -> int:
        try:
            from importlib.metadata import version

            return int(version("pywebview").split(".")[0])
        except Exception:
            return 6

    def initial_window_pos(self) -> Optional[tuple[int, int]]:
        """Última posição da janela, se ainda cair dentro da área de tela atual."""
        pos = self._settings.get("window_pos")
        if not pos:
            return None
        try:
            vx, vy, vw, vh = sendinput.get_virtual_screen_rect()
        except Exception:
            return None
        x, y = int(pos[0]), int(pos[1])
        # Exige que um pedaço útil da barra de título fique visível.
        if vx - 200 <= x <= vx + vw - 120 and vy <= y <= vy + vh - 80:
            return x, y
        return None

    def _on_window_moved(self, x: Any = None, y: Any = None) -> None:
        try:
            if x is None or y is None:
                x, y = self._window.x, self._window.y
            self._settings.update({"window_pos": [int(x), int(y)]}, defer=True)
        except Exception:
            pass

    def _restore_last_macro(self) -> None:
        """Recarrega a macro salva usada por último (para agendamentos e para o Reproduzir)."""
        name = self._settings.get("macro")["name"]
        if not name:
            return
        try:
            self._macro_recorder.set_events(self._macros.load(name))
        except (ValueError, OSError):
            log.info("Macro %r não pôde ser recarregada", name)
            prefs = self._settings.get("macro")
            prefs["name"] = ""
            self._settings.update({"macro": prefs})

    def _restore_last_config(self) -> None:
        last = self._settings.get("last_config")
        if not last:
            return
        try:
            self._engine.update_config(last)
        except (TypeError, ValueError):
            log.warning("Última configuração salva é inválida; usando padrões")

    def bootstrap_services(self) -> None:
        """Inicia hotkey global, bandeja e aplica always-on-top."""
        try:
            self._hotkeys.start()
        except Exception:
            log.exception("Falha ao iniciar hotkeys globais")
        self._apply_always_on_top(bool(self._settings.get("always_on_top")))
        self.start_tray()
        self._engine.set_click_guard(self._click_guard)
        self._engine.set_key_guard(self._key_guard)
        self._macro_recorder.set_ignore_point(self._click_guard)
        signal = self._notifier.signal
        self._engine.set_on_tick(signal)
        self._macro_recorder.set_on_change(signal)
        self._macro_player.set_on_tick(signal)
        self._macro_player.set_on_done(signal)
        self._scheduler.set_on_change(signal)
        self._scheduler.set_on_fire(self._on_schedule_fire)
        saved_schedule = self._settings.get("schedule")
        if saved_schedule and not self._scheduler.restore(saved_schedule):
            self._settings.update({"schedule": None})
        self._script.set_on_tick(signal)
        self._script.set_on_done(signal)
        self._ui_alive = True
        self._notifier.start()
        self._refresh_autostart()
        if self._settings.get("check_updates"):
            self._check_updates_async()

    def start_tray(self, detached: bool = False) -> None:
        """
        Cria o ícone da bandeja (idempotente). Falha aqui não derruba o app:
        sem bandeja, fechar a janela encerra o programa de verdade.
        """
        if self._tray is not None:
            return
        try:
            from app.tray import SystemTray

            tray = SystemTray(
                on_show=self._tray_show,
                on_hide=self._tray_hide,
                on_quit=self._tray_quit,
                on_toggle=self._tray_toggle,
                locale=self._settings.get_locale(),
            )
            tray.start(detached=detached)
            self._tray = tray
        except Exception:
            log.exception("Bandeja do sistema indisponível")
            self._tray = None

    def shutdown(self) -> None:
        # Impede evaluate_js em WebView2 já descartado (ticks/hotkey em corrida com destroy).
        self._ui_alive = False
        self._notifier.stop()
        self._clear_ui_callbacks()
        # Encerra a thread sem apagar o agendamento salvo (ele volta no próximo início).
        self._scheduler.set_on_fire(None)
        self._scheduler.shutdown()
        self._macro_recorder.stop()
        self._macro_player.stop()
        self._script.stop()
        self._engine.stop()
        try:
            self._hotkeys.stop()
        except Exception:
            log.exception("Falha ao parar hotkeys")
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                log.exception("Falha ao parar a bandeja")
            self._tray = None
        self._cancel_wf_capture()
        self._close_overlay()
        self._close_info()
        self._settings.flush()
        self._window = None

    def _clear_ui_callbacks(self) -> None:
        self._engine.set_on_tick(None)
        self._macro_recorder.set_on_change(None)
        self._macro_player.set_on_tick(None)
        self._macro_player.set_on_done(None)
        self._scheduler.set_on_change(None)
        self._script.set_on_tick(None)
        self._script.set_on_done(None)

    def has_tray(self) -> bool:
        return self._tray is not None

    def mark_window_hidden(self) -> None:
        """A janela foi criada oculta (início minimizado na bandeja)."""
        self._window_visible = False

    def should_close_to_tray(self) -> bool:
        """True se o fechamento da janela deve apenas ocultar (não encerrar)."""
        return not self._quit_requested and self._tray is not None

    def _clear_errors(self) -> None:
        self._error = None
        self._engine.set_last_error(None)
        self._macro_player.clear_error()
        self._script.clear_error()
        self._scheduler.clear_error()

    def _fail(self, code: str, message: str = "", **params: Any) -> None:
        self._error = ClickrError(code, message, **params).to_dict()

    # --- Bridge JS API -------------------------------------------------

    @api
    def start(self) -> dict[str, Any]:
        self._stop_tier3_runners(keep_schedule=True)
        self._engine.start()
        return self.get_state()

    @api
    def stop(self) -> dict[str, Any]:
        self._engine.stop()
        self._macro_player.stop()
        self._script.stop()
        return self.get_state()

    def get_state(self) -> dict[str, Any]:
        state = self._engine.get_state().to_dict()
        state["picking"] = self._picking
        state["recording_hotkey"] = self._recording_hotkey
        state["recording_hotkey_action"] = self._recording_hotkey_action
        macro_playing = self._macro_player.is_playing()
        macro_recording = self._macro_recorder.is_recording()
        script_status = self._script.status()
        sched = self._scheduler.status()
        # Um único erro por vez, na ordem: ação da UI, motor, macro, script, agenda.
        state["last_error"] = (
            self._error
            or normalize_error(state.get("last_error"))
            or self._macro_player.last_error()
            or script_status.get("last_error")
            or sched.get("last_error")
        )
        macro_prefs = self._settings.get("macro")
        progress = self._macro_player.progress()
        state["macro"] = {
            "recording": macro_recording,
            "playing": macro_playing,
            "event_count": self._macro_recorder.event_count(),
            "duration_ms": self._macro_recorder.duration_ms(),
            "iteration": progress["iteration"] if macro_playing else 0,
            "repeat": macro_prefs["repeat"],
            "speed": macro_prefs["speed"],
            "name": macro_prefs["name"],
        }
        state["schedule"] = {
            key: sched[key]
            for key in ("active", "at", "repeat", "interval_s", "target", "profile")
        }
        state["script"] = {
            "running": script_status["running"],
            "line": script_status["line"],
        }
        state["window_capture"] = {
            "active": self._wf_capture_until is not None,
            "ends_at": self._wf_capture_until,
        }
        state["update"] = self._update_info
        state["settings"] = self._public_settings()
        state["engine_running"] = bool(state["running"])
        state["running"] = bool(state["running"] or macro_playing or script_status["running"])
        return state

    _PUBLIC_SETTINGS = (
        "hotkeys",
        "activation",
        "always_on_top",
        "compact_mode",
        "time_units",
        "launch_at_login",
        "check_updates",
    )

    def _public_settings(self) -> dict[str, Any]:
        return self._settings.pick(self._PUBLIC_SETTINGS)

    def _state_with_profiles(self) -> dict[str, Any]:
        state = self.get_state()
        state["profiles"] = self._profiles.list_profiles()
        return state

    @api
    def set_config(self, config: Optional[dict[str, Any]] = None, **kwargs: Any) -> dict[str, Any]:
        """
        Atualiza configuração parcial.

        Aceita dict (via JSON do JS) ou kwargs.
        Ao entrar em mode fixed sem XY explícitos úteis, captura cursor atual.
        """
        data: dict[str, Any] = {}
        if isinstance(config, dict):
            data.update(config)
        data.update(kwargs)

        current = self._engine.get_config()
        incoming_mode = data.get("position_mode", current.position_mode)
        has_xy = "fixed_x" in data or "fixed_y" in data

        if incoming_mode == "fixed" and not has_xy:
            if current.position_mode != "fixed" or (current.fixed_x == 0 and current.fixed_y == 0):
                x, y = sendinput.get_cursor_pos()
                data.setdefault("fixed_x", x)
                data.setdefault("fixed_y", y)

        if data.get("click_type") == "hold":
            data["hold"] = True
        elif data.get("click_type") in ("single", "double"):
            data["hold"] = False
        elif data.get("hold") is True:
            data["click_type"] = "hold"
        elif data.get("hold") is False and current.click_type == "hold":
            data.setdefault("click_type", "single")

        # Merge parcial de window_filter
        if "window_filter" in data and isinstance(data["window_filter"], dict):
            merged_wf = current.window_filter.to_dict()
            merged_wf.update(data["window_filter"])
            data["window_filter"] = merged_wf

        self._apply_config(data)
        return self.get_state()

    @api
    def set_compact_mode(self, enabled: bool) -> dict[str, Any]:
        self._apply_prefs({"compact_mode": bool(enabled)})
        return self.get_state()

    @api
    def set_preferences(self, values: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Atualiza preferências do aplicativo (não fazem parte dos perfis)."""
        self._apply_prefs(dict(values or {}))
        return self.get_state()

    @api
    def check_updates_now(self) -> dict[str, Any]:
        """Consulta o GitHub Releases agora (independente da opção automática)."""
        self._check_updates_async()
        return self.get_state()

    def open_update_page(self) -> dict[str, Any]:
        """Abre no navegador a página da versão nova (sempre no repositório do projeto)."""
        import webbrowser

        url = updates.safe_release_url((self._update_info or {}).get("url"))
        try:
            webbrowser.open(url)
        except Exception:
            log.exception("Falha ao abrir o navegador")
            return {"ok": False, "url": url}
        return {"ok": True, "url": url}

    def save_script(self, source: str = "") -> dict[str, Any]:
        """Guarda o texto do editor de script para a próxima sessão."""
        self._settings.update({"last_script": str(source or "")}, defer=True)
        return {"ok": True}

    def set_manual_seen(self, seen: bool = True) -> dict[str, Any]:
        self._settings.update({"manual_seen": bool(seen)})
        return {"ok": True}

    @api
    def pick_location(self, target: str = "fixed", delay_ms: int = 0) -> dict[str, Any]:
        """
        Abre overlay cobrindo a tela virtual para capturar XY (não bloqueia a bridge).

        target="fixed" define o ponto fixo; target="sequence" acrescenta o ponto
        à sequência com o delay informado.
        """
        if self._picking:
            return self.get_state()
        self._pick_target = "sequence" if str(target) == "sequence" else "fixed"
        try:
            self._pick_delay_ms = max(0, int(delay_ms or 0))
        except (TypeError, ValueError):
            self._pick_delay_ms = 0
        overlay_path = (UI_DIR / "overlay.html").resolve()
        if not overlay_path.is_file():
            raise ClickrError("overlayMissing", f"Overlay não encontrado: {overlay_path}")

        self._close_overlay()
        self._picking = True
        try:
            vx, vy, vw, vh = sendinput.get_virtual_screen_rect()
            # Uma janela transparente cobrindo a tela virtual (todos os monitores):
            # o usuário enxerga o que está por baixo enquanto escolhe o ponto.
            overlay = webview.create_window(
                title=self._ui_string("overlay.windowTitle", "Clickr — capturar ponto"),
                url=overlay_path.as_uri(),
                js_api=self,
                x=vx,
                y=vy,
                width=vw,
                height=vh,
                fullscreen=False,
                on_top=True,
                frameless=True,
                easy_drag=False,
                resizable=False,
                transparent=self._transparent_overlay_supported(),
                # Só aparece se o backend do SO ignorar a transparência.
                background_color="#000000",
            )
            self._overlay = overlay
            # Fechamento por qualquer via (Alt+F4, SO) não pode travar o estado.
            try:
                overlay.events.closed += self._on_overlay_closed
            except Exception:
                log.exception("Não foi possível observar o fechamento do overlay")
        except Exception:
            self._picking = False
            self._overlay = None
            raise
        self._notifier.signal()
        return self.get_state()

    @api
    def confirm_pick(self, x: int = 0, y: int = 0) -> dict[str, Any]:
        """Callback do overlay: usa posição real do cursor e fecha a captura."""
        cx, cy = sendinput.get_cursor_pos()
        self._picking = False
        self._close_overlay()
        if self._pick_target == "sequence":
            steps = self._sequence_steps()
            steps.append({"x": int(cx), "y": int(cy), "delay_ms": self._pick_delay_ms})
            self._apply_config({"sequence": steps})
        else:
            self._apply_config(
                {
                    "position_mode": "fixed",
                    "fixed_x": int(cx),
                    "fixed_y": int(cy),
                }
            )
        self._notifier.signal()
        return self.get_state()

    @api
    def cancel_pick(self) -> dict[str, Any]:
        self._picking = False
        self._close_overlay()
        self._notifier.signal()
        return self.get_state()

    @api
    def add_sequence_point(
        self, x: Optional[int] = None, y: Optional[int] = None, delay_ms: int = 0
    ) -> dict[str, Any]:
        """Adiciona um passo à sequência (XY atuais do cursor se omitidos)."""
        if x is None or y is None:
            cx, cy = sendinput.get_cursor_pos()
            x = cx if x is None else int(x)
            y = cy if y is None else int(y)
        steps = self._sequence_steps()
        steps.append({"x": int(x), "y": int(y), "delay_ms": max(0, int(delay_ms or 0))})
        self._apply_config({"sequence": steps})
        return self.get_state()

    @api
    def remove_sequence_point(self, index: int) -> dict[str, Any]:
        steps = self._sequence_steps()
        steps.pop(self._sequence_index(index, len(steps)))
        self._apply_config({"sequence": steps})
        return self.get_state()

    @api
    def update_sequence_point(
        self, index: int, patch: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Edita x, y e/ou delay_ms de um passo da sequência."""
        steps = self._sequence_steps()
        idx = self._sequence_index(index, len(steps))
        for key in ("x", "y", "delay_ms"):
            if patch and patch.get(key) is not None:
                try:
                    value = int(patch[key])
                except (TypeError, ValueError):
                    raise ClickrError("config.invalid", "Valor inválido para o passo") from None
                steps[idx][key] = max(0, value) if key == "delay_ms" else value
        self._apply_config({"sequence": steps})
        return self.get_state()

    @api
    def move_sequence_point(self, index: int, to: int) -> dict[str, Any]:
        """Move um passo da sequência para outra posição da lista."""
        steps = self._sequence_steps()
        src = self._sequence_index(index, len(steps))
        dst = self._sequence_index(to, len(steps))
        steps.insert(dst, steps.pop(src))
        self._apply_config({"sequence": steps})
        return self.get_state()

    @api
    def capture_foreground_window(self, delay_s: float = 3.0) -> dict[str, Any]:
        """
        Após `delay_s` segundos, lê a janela em foco e preenche o filtro de
        janela (processo e título). Dá tempo de o usuário trocar para o alvo.
        """
        try:
            delay = min(30.0, max(0.5, float(delay_s)))
        except (TypeError, ValueError):
            delay = 3.0
        self._cancel_wf_capture()
        self._wf_capture_until = time.time() + delay
        timer = threading.Timer(delay, self._finish_wf_capture)
        timer.daemon = True
        self._wf_capture_timer = timer
        timer.start()
        return self.get_state()

    @api
    def cancel_capture_foreground_window(self) -> dict[str, Any]:
        self._cancel_wf_capture()
        return self.get_state()

    @api
    def clear_sequence(self) -> dict[str, Any]:
        self._apply_config({"sequence": []})
        return self.get_state()

    @api
    def record_hotkey(self, action: str = "toggle") -> dict[str, Any]:
        """Inicia a captura do próximo combo de teclas para a ação informada."""
        if self._recording_hotkey:
            return self.get_state()
        action = str(action or "toggle")
        if action not in HOTKEY_ACTIONS:
            raise ClickrError("hotkey.unknownAction", f"Ação de atalho desconhecida: {action}")
        self._recording_hotkey = True
        self._recording_hotkey_action = action
        try:
            self._hotkeys.begin_capture(lambda text: self._on_hotkey_captured(action, text))
        except Exception:
            self._recording_hotkey = False
            self._recording_hotkey_action = ""
            raise
        self._notifier.signal()
        return self.get_state()

    @api
    def cancel_record_hotkey(self) -> dict[str, Any]:
        self._hotkeys.cancel_capture()
        self._recording_hotkey = False
        self._recording_hotkey_action = ""
        self._notifier.signal()
        return self.get_state()

    @api
    def capture_action_key(self) -> dict[str, Any]:
        """Captura a próxima tecla/combinação como a tecla do autoclique de teclado."""
        if self._recording_hotkey:
            return self.get_state()
        self._recording_hotkey = True
        self._recording_hotkey_action = "action_key"
        try:
            self._hotkeys.begin_capture(self._on_action_key_captured)
        except Exception:
            self._recording_hotkey = False
            self._recording_hotkey_action = ""
            raise
        self._notifier.signal()
        return self.get_state()

    @api
    def set_hotkey(self, action: str = "toggle", combo: str = "") -> dict[str, Any]:
        """Define o atalho de uma ação por texto (ex.: 'CTRL+ALT+F6'); vazio remove."""
        self._set_hotkey(str(action or "toggle"), str(combo or ""))
        return self.get_state()

    @api
    def clear_hotkey(self, action: str) -> dict[str, Any]:
        self._set_hotkey(str(action or ""), "")
        return self.get_state()

    # --- Macro ---------------------------------------------------------

    @api
    def macro_record_start(self) -> dict[str, Any]:
        if self._macro_recorder.is_recording():
            return self.get_state()
        self._stop_tier3_runners(keep_schedule=True)
        self._engine.stop()
        if not self._macro_recorder.start():
            self._fail("macro.recordFailed", "Não foi possível iniciar a gravação da macro.")
        return self.get_state()

    @api
    def macro_record_stop(self) -> dict[str, Any]:
        # Se a gravação começou pelo atalho, a soltura dessas teclas é descartada.
        combo = self._hotkeys.combo("macro_record")
        self._macro_recorder.stop(strip_tokens=combo.tokens() if combo is not None else None)
        return self.get_state()

    @api
    def macro_play(self, repeat: Any = None, speed: Any = None) -> dict[str, Any]:
        """Reproduz a macro atual. repeat/speed omitidos usam os últimos valores."""
        if self._macro_player.is_playing():
            return self.get_state()
        prefs = self._settings.get("macro")
        if repeat is not None or speed is not None:
            prefs = self._save_macro_prefs(repeat=repeat, speed=speed)
        events = self._macro_recorder.get_events()
        if self._macro_recorder.is_recording():
            self._macro_recorder.stop()
        self._engine.stop()
        self._script.stop()
        self._macro_player.play(events, repeat=prefs["repeat"], speed=prefs["speed"])
        return self.get_state()

    @api
    def macro_set_options(self, repeat: Any = None, speed: Any = None) -> dict[str, Any]:
        self._save_macro_prefs(repeat=repeat, speed=speed)
        return self.get_state()

    def list_macros(self) -> list[str]:
        try:
            return self._macros.list_macros()
        except OSError:
            log.exception("Falha ao listar macros")
            return []

    def _state_with_macros(self) -> dict[str, Any]:
        state = self.get_state()
        state["macros"] = self.list_macros()
        return state

    @api
    def macro_save(self, name: str) -> dict[str, Any]:
        if self._macro_recorder.is_recording():
            raise ClickrError("macro.busy", "Pare a macro antes de salvar.")
        saved = self._macros.save(name, self._macro_recorder.get_events())
        self._save_macro_prefs(name=saved)
        state = self._state_with_macros()
        state["saved_macro"] = saved
        return state

    @api
    def macro_load(self, name: str) -> dict[str, Any]:
        if self._macro_recorder.is_recording() or self._macro_player.is_playing():
            raise ClickrError("macro.busy", "Pare a macro antes de carregar outra.")
        events = self._macros.load(name)
        self._macro_recorder.set_events(events)
        self._save_macro_prefs(name=str(name).strip())
        return self._state_with_macros()

    @api
    def macro_delete(self, name: str) -> dict[str, Any]:
        deleted = self._macros.delete(name)
        if self._settings.get("macro")["name"] == deleted:
            self._save_macro_prefs(name="")
        return self._state_with_macros()

    def _save_macro_prefs(
        self, repeat: Any = None, speed: Any = None, name: Optional[str] = None
    ) -> dict[str, Any]:
        prefs = self._settings.get("macro")
        try:
            if repeat is not None:
                prefs["repeat"] = int(repeat)
            if speed is not None:
                prefs["speed"] = float(speed)
        except (TypeError, ValueError):
            raise ClickrError("macro.badOptions", "Repetições ou velocidade inválidas.") from None
        if name is not None:
            prefs["name"] = name
        return self._settings.update({"macro": prefs})["macro"]

    @api
    def macro_stop(self) -> dict[str, Any]:
        if self._macro_recorder.is_recording():
            self._macro_recorder.stop()
        self._macro_player.stop()
        return self.get_state()

    @api
    def macro_clear(self) -> dict[str, Any]:
        if self._macro_recorder.is_recording() or self._macro_player.is_playing():
            self._fail("macro.busy", "Pare a macro antes de limpar.")
            return self.get_state()
        self._macro_recorder.clear()
        self._save_macro_prefs(name="")
        return self.get_state()

    # --- Scheduler -----------------------------------------------------

    @api
    def schedule_set(self, when: str, options: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Agenda um disparo. when: ISO local 'YYYY-MM-DDTHH:MM[:SS]'.
        options: repeat (once|daily|interval), interval_s, target
        (engine|macro|script|profile) e profile.
        """
        opts = dict(options or {})
        if opts.get("target") == "profile" and not self._profiles.exists(
            str(opts.get("profile") or "")
        ):
            raise ClickrError(
                "profile.notFound",
                f"Perfil não encontrado: {opts.get('profile')}",
                name=str(opts.get("profile") or ""),
            )
        self._scheduler.schedule(
            (when or "").strip(),
            repeat=opts.get("repeat"),
            interval_s=opts.get("interval_s"),
            target=opts.get("target"),
            profile=opts.get("profile"),
        )
        self._settings.update({"schedule": self._scheduler.to_dict()})
        return self.get_state()

    @api
    def schedule_cancel(self) -> dict[str, Any]:
        self._scheduler.cancel()
        self._settings.update({"schedule": None})
        return self.get_state()

    # --- Script --------------------------------------------------------

    @api
    def script_run(self, source: str = "") -> dict[str, Any]:
        if self._script.is_running():
            return self.get_state()
        self._engine.stop()
        self._macro_player.stop()
        if self._macro_recorder.is_recording():
            self._macro_recorder.stop()
        self._settings.update({"last_script": str(source or "")}, defer=True)
        self._script.run(source or "")
        return self.get_state()

    @api
    def script_stop(self) -> dict[str, Any]:
        self._script.stop()
        return self.get_state()

    # --- Perfis --------------------------------------------------------

    def list_profiles(self) -> list[str]:
        try:
            return self._profiles.list_profiles()
        except OSError:
            log.exception("Falha ao listar perfis")
            return []

    @api
    def save_profile(self, name: str) -> dict[str, Any]:
        cfg = self._engine.get_config().to_dict()
        saved = self._profiles.save(name, cfg)
        state = self._state_with_profiles()
        state["saved_profile"] = saved
        return state

    @api
    def load_profile(self, name: str) -> dict[str, Any]:
        self._load_profile_document(self._profiles.load_document(name))
        return self._state_with_profiles()

    def _load_profile_document(self, document: dict[str, Any]) -> None:
        """
        Aplica um perfil. Perfis da versão 1 também carregavam atalho, "sempre no
        topo" e modo compacto: esse comportamento é mantido para eles. Perfis v2
        guardam só a configuração de clique e não alteram preferências do app.
        """
        config = dict(document["config"])
        if int(document.get("version", 1) or 1) >= PROFILE_VERSION:
            self._apply_config(config, allow_prefs=False, replace=True)
            return
        # v1: mesma mescla sobre a config atual que a 1.0.x fazia; campos que
        # não existiam naquela versão voltam ao padrão (= comportamento antigo).
        defaults = ClickConfig().to_dict()
        merged = {k: v for k, v in defaults.items() if k not in V1_CONFIG_KEYS}
        merged.update(config)
        self._apply_config(merged, allow_prefs=True)

    @api
    def delete_profile(self, name: str) -> dict[str, Any]:
        deleted = self._profiles.delete(name)
        state = self._state_with_profiles()
        state["deleted_profile"] = deleted
        return state

    @api
    def rename_profile(self, old: str, new: str) -> dict[str, Any]:
        renamed = self._profiles.rename(old, new)
        # Um agendamento que apontava para o nome antigo acompanha a mudança.
        sched = self._scheduler.to_dict()
        if sched and sched.get("target") == "profile" and sched.get("profile") == str(old).strip():
            sched["profile"] = renamed
            if self._scheduler.restore(sched):
                self._settings.update({"schedule": self._scheduler.to_dict()})
        state = self._state_with_profiles()
        state["renamed_profile"] = renamed
        return state

    @api
    def export_profile(self, name: str = "") -> dict[str, Any]:
        """Abre diálogo Salvar e exporta perfil (salvo ou config atual) em JSON."""
        label = (name or "").strip() or "clickr-perfil"
        safe_name = ProfilesRepo.validate_new_name(label)
        result = self._file_dialog(
            webview.SAVE_DIALOG,
            save_filename=f"{safe_name}.json",
            file_types=("JSON (*.json)",),
        )
        if not result:
            return self.get_state()
        dest = Path(result[0] if isinstance(result, (list, tuple)) else result)
        if self._profiles.exists(safe_name):
            self._profiles.export_to(safe_name, dest)
        else:
            self._profiles.export_config(safe_name, self._engine.get_config().to_dict(), dest)
        state = self.get_state()
        state["exported_path"] = str(dest)
        return state

    @api
    def import_profile(self, name: str = "") -> dict[str, Any]:
        """
        Abre diálogo Abrir e importa JSON para a pasta de perfis.

        Se já existir um perfil com o nome resultante, nada é gravado: o estado
        volta com `import_conflict` e a UI pede confirmação antes de chamar
        import_profile_confirm().
        """
        result = self._file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("JSON (*.json)",),
        )
        if not result:
            return self.get_state()
        src = Path(result[0] if isinstance(result, (list, tuple)) else result)
        override = (name or "").strip() or None
        target = self._profiles.resolve_import_name(src, override)
        if self._profiles.exists(target):
            self._pending_import = (src, target)
            state = self.get_state()
            state["import_conflict"] = target
            return state
        return self._finish_import(src, target)

    @api
    def import_profile_confirm(self) -> dict[str, Any]:
        """Conclui a importação pendente, sobrescrevendo o perfil existente."""
        pending, self._pending_import = self._pending_import, None
        if not pending:
            return self.get_state()
        return self._finish_import(*pending)

    def _finish_import(self, src: Path, name: str) -> dict[str, Any]:
        saved = self._profiles.import_from(src, name=name)
        self._load_profile_document(self._profiles.load_document(saved))
        state = self._state_with_profiles()
        state["imported_profile"] = saved
        return state

    @api
    def set_always_on_top(self, enabled: bool) -> dict[str, Any]:
        self._apply_prefs({"always_on_top": bool(enabled)})
        return self.get_state()

    # --- Janela --------------------------------------------------------

    def show_window(self) -> None:
        self._tray_show()

    def hide_window(self, notify: bool = False) -> None:
        """Oculta a janela. Se notify=True, avisa que o app segue na bandeja."""
        # O aviso "continua na bandeja" aparece só na primeira vez.
        if notify and self._tray is not None and not self._settings.get("tray_hint_shown"):
            try:
                self._tray.notify_still_running()
            except Exception:
                # Nem todo SO suporta notificação pela bandeja (ex.: macOS).
                log.info("Notificação da bandeja indisponível neste sistema")
            self._settings.update({"tray_hint_shown": True})
        self._tray_hide()

    def get_settings(self) -> dict[str, Any]:
        """Preferências do app (locale) + versão do arquivo VERSION."""
        data = self._settings.load()
        out = self._public_settings()
        out.update(
            {
                "locale": data.get("locale"),
                "supported_locales": list(SUPPORTED_LOCALES),
                "version": self._version(),
                "profiles": self.list_profiles(),
                "macros": self.list_macros(),
                "manual_seen": bool(data.get("manual_seen")),
                "tray_hint_shown": bool(data.get("tray_hint_shown")),
                "last_script": data.get("last_script") or "",
            }
        )
        return out

    def set_locale(self, code: str) -> dict[str, Any]:
        """Persiste locale, atualiza menu da bandeja e devolve settings."""
        saved = self._settings.set_locale(str(code or "").strip())
        if self._tray is not None and saved.get("locale"):
            try:
                self._tray.set_locale(str(saved["locale"]))
            except Exception:
                log.exception("Falha ao atualizar idioma da bandeja")
        return {
            "locale": saved.get("locale"),
            "supported_locales": list(SUPPORTED_LOCALES),
            "version": self._version(),
        }

    def window_minimize(self) -> None:
        """Minimiza a janela principal (title bar custom)."""
        if self._window is None:
            raise RuntimeError("Janela não anexada")
        self._window.minimize()

    def window_close(self) -> None:
        """Fecha para a bandeja e notifica o usuário (ou encerra, se não há bandeja)."""
        if self._tray is None:
            self._tray_quit()
            return
        self.hide_window(notify=True)

    def show_info_popup(self, title: str, body_html: str) -> dict[str, Any]:
        """Abre janela auxiliar fora da principal com texto de ajuda (Assistente)."""
        info_path = (UI_DIR / "info.html").resolve()
        if not info_path.is_file():
            raise FileNotFoundError(f"info.html não encontrado: {info_path}")

        clean_title = str(title or "Informação").strip() or "Informação"
        self._info_payload = {
            "title": clean_title,
            "body_html": str(body_html or ""),
        }
        self._close_info()

        x, y = 120, 120
        main = self._window
        if main is not None:
            try:
                x, y = self.to_create_coords(int(main.x) + int(main.width) + 16, int(main.y))
            except Exception:
                pass

        self._info = webview.create_window(
            title=f"Clickr — {clean_title[:48]}",
            url=info_path.as_uri(),
            js_api=self,
            x=x,
            y=y,
            width=360,
            height=400,
            resizable=True,
            on_top=True,
            frameless=True,
            easy_drag=False,
            background_color="#14100c",
        )
        return {"ok": True, "title": clean_title}

    def get_info_popup(self) -> dict[str, str]:
        """Conteúdo da janela de info (lido pelo info.html)."""
        return dict(self._info_payload)

    def close_info_popup(self) -> dict[str, Any]:
        self._close_info()
        return {"ok": True}

    # --- Interno -------------------------------------------------------

    @staticmethod
    def _version() -> str:
        try:
            return app_version()
        except (OSError, ValueError):
            log.exception("VERSION ilegível")
            return ""

    def _file_dialog(self, dialog_type: Any, **kwargs: Any) -> Any:
        window = self._window
        if window is not None and hasattr(window, "create_file_dialog"):
            return window.create_file_dialog(dialog_type, **kwargs)
        return webview.create_file_dialog(dialog_type, **kwargs)

    def _sequence_steps(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._engine.get_config().sequence]

    @staticmethod
    def _sequence_index(index: Any, length: int) -> int:
        try:
            idx = int(index)
        except (TypeError, ValueError):
            idx = -1
        if idx < 0 or idx >= length:
            raise ClickrError("sequence.badIndex", "Índice de sequência inválido")
        return idx

    def _apply_config(
        self, data: dict[str, Any], allow_prefs: bool = True, replace: bool = False
    ) -> ClickConfig:
        """
        Aplica config de clique no motor e a guarda como "última configuração".

        Chaves de preferência do app (hotkey, always_on_top, compact_mode) que
        venham junto são encaminhadas a _apply_prefs quando allow_prefs=True
        (UI e perfis v1) ou descartadas (perfis v2). replace=True parte dos
        padrões em vez da config atual (carga de perfil).
        """
        data = dict(data)
        prefs = {key: data.pop(key) for key in LEGACY_APP_KEYS if key in data}
        if data.get("key_name") is not None:
            try:
                parse_key_sequence(str(data["key_name"]))
            except ValueError:
                bad = str(data.pop("key_name"))
                self._fail("key.unsupported", f"Tecla não suportada: {bad}", key=bad)
        try:
            if replace:
                data = ClickConfig.from_dict(data).to_dict()
            updated = self._engine.update_config(data)
        except (TypeError, ValueError) as exc:
            if isinstance(exc, ClickrError):
                raise
            raise ClickrError("config.invalid", f"Configuração inválida: {exc}") from exc
        self._settings.update({"last_config": updated.to_dict()}, defer=True)
        if allow_prefs and prefs:
            self._apply_prefs(prefs)
        return updated

    def _apply_prefs(self, values: dict[str, Any]) -> None:
        """Valida e grava preferências do aplicativo, aplicando seus efeitos."""
        changes: dict[str, Any] = {}
        if values.get("hotkey") is not None:
            # Chave legada (perfis v1 / UI antiga): atalho de iniciar/parar.
            try:
                self._set_hotkey("toggle", str(values["hotkey"]))
            except ClickrError as exc:
                self._error = exc.to_dict()
        if values.get("activation") is not None and values["activation"] not in ACTIVATION_MODES:
            values = {k: v for k, v in values.items() if k != "activation"}
        for key in ("always_on_top", "compact_mode", "check_updates"):
            if key in values and values[key] is not None:
                changes[key] = bool(values[key])
        if values.get("launch_at_login") is not None:
            wanted = bool(values["launch_at_login"])
            try:
                autostart.set_enabled(wanted)
                changes["launch_at_login"] = wanted
            except Exception as exc:  # noqa: BLE001 - registro/arquivo do SO
                log.exception("Falha ao configurar início automático")
                self._fail("autostart.failed", f"Não foi possível alterar o início automático: {exc}")
        for key in ("time_units", "activation"):
            if key in values and values[key] is not None:
                if key == "time_units" and isinstance(values[key], dict):
                    merged = self._settings.get("time_units")
                    merged.update(values[key])
                    changes[key] = merged
                else:
                    changes[key] = values[key]
        if not changes:
            return
        self._settings.update(changes)
        if "always_on_top" in changes:
            self._apply_always_on_top(bool(self._settings.get("always_on_top")))
        if changes.get("check_updates"):
            self._check_updates_async()

    def _refresh_autostart(self) -> None:
        """Mantém o registro de início automático apontando para este executável."""
        try:
            if self._settings.get("launch_at_login"):
                autostart.set_enabled(True)
        except Exception:
            log.exception("Falha ao atualizar o início automático")

    def _check_updates_async(self) -> None:
        if self._update_checking:
            return
        self._update_checking = True

        def run() -> None:
            try:
                self._update_info = updates.check_latest(self._version())
            except Exception as exc:  # noqa: BLE001 - rede indisponível é esperado
                log.info("Verificação de atualização falhou: %s", exc)
            finally:
                self._update_checking = False
            self._notifier.signal()

        threading.Thread(target=run, name="UpdateCheck", daemon=True).start()

    def _stop_tier3_runners(self, keep_schedule: bool = False) -> None:
        if self._macro_recorder.is_recording():
            self._macro_recorder.stop()
        self._macro_player.stop()
        self._script.stop()
        if not keep_schedule:
            self._scheduler.cancel()
            self._settings.update({"schedule": None})

    def _on_schedule_fire(self, item: Optional[dict[str, Any]] = None) -> None:
        """Executa o alvo do agendamento (chamado pela thread do Scheduler)."""
        target = (item or {}).get("target") or "engine"
        self._clear_errors()
        self._stop_tier3_runners(keep_schedule=True)
        if target == "macro":
            self._engine.stop()
            prefs = self._settings.get("macro")
            self._macro_player.play(
                self._macro_recorder.get_events(), repeat=prefs["repeat"], speed=prefs["speed"]
            )
        elif target == "script":
            self._engine.stop()
            self._script.run(self._settings.get("last_script") or "")
        else:
            if target == "profile":
                self._engine.stop()
                self._load_profile_document(
                    self._profiles.load_document(str((item or {}).get("profile") or ""))
                )
            self._engine.start()
        # Recorrentes continuam ativos; o disparo único some do arquivo.
        self._settings.update({"schedule": self._scheduler.to_dict()})
        self._notifier.signal()

    def _apply_always_on_top(self, enabled: bool) -> None:
        window = self._window
        if window is None:
            return
        try:
            window.on_top = bool(enabled)
        except Exception as exc:
            log.exception("Falha ao aplicar always-on-top")
            self._fail("alwaysOnTop", f"Falha ao aplicar always-on-top: {exc}")

    def _set_hotkey(self, action: str, combo: str) -> str:
        """Valida, aplica no serviço e persiste o atalho de uma ação."""
        if action == "toggle" and not combo.strip():
            raise ClickrError(
                "hotkey.toggleRequired", "O atalho de iniciar/parar não pode ficar vazio."
            )
        name = self._hotkeys.set_binding(action, combo)
        self._settings.update({"hotkeys": self._hotkeys.bindings()})
        return name

    def _on_hotkey_captured(self, action: str, text: str) -> None:
        self._recording_hotkey = False
        self._recording_hotkey_action = ""
        self._clear_errors()
        if text:  # vazio = cancelado com ESC
            try:
                self._set_hotkey(action, text)
            except ClickrError as exc:
                self._error = exc.to_dict()
        self._notifier.signal()

    def _on_action_key_captured(self, text: str) -> None:
        self._recording_hotkey = False
        self._recording_hotkey_action = ""
        self._clear_errors()
        if text:
            try:
                self._apply_config({"action": "key", "key_name": text})
            except ClickrError as exc:
                self._error = exc.to_dict()
        self._notifier.signal()

    def _on_hotkey_action(self, action: str) -> None:
        """Chamado pela thread de despacho do HotkeyService."""
        if self._recording_hotkey:
            return
        try:
            if action == "stop_all":
                self._stop_everything()
            elif self._picking:
                return
            elif action == "toggle":
                self._toggle_from_hotkey()
            elif action == "pick_point":
                self._pick_point_at_cursor()
            elif action == "macro_record":
                self._toggle_macro_record_from_hotkey()
        except Exception:
            log.exception("Falha ao executar atalho %s", action)
        self._notifier.signal()

    def _stop_everything(self) -> None:
        """Parada de emergência: motor, macro (gravação e reprodução), script e captura."""
        if self._picking:
            self._picking = False
            self._close_overlay()
        if self._macro_recorder.is_recording():
            self._macro_recorder.stop()
        self._macro_player.stop()
        self._script.stop()
        self._engine.stop()

    def _toggle_from_hotkey(self) -> None:
        if self._macro_recorder.is_recording():
            return
        if self._macro_player.is_playing():
            self._macro_player.stop()
            return
        if self._script.is_running():
            self._script.stop()
            return
        if self._settings.get("activation") == "hold":
            self._start_while_held()
            return
        self._engine.toggle()

    def _start_while_held(self) -> None:
        """Modo "segurar": o motor roda enquanto a tecla do atalho estiver pressionada."""
        if self._engine.is_running():
            # Tecla já solta e pressionada de novo antes do motor parar: encerra.
            self._engine.stop()
            return
        self._engine.start()

        def watch() -> None:
            # Dá tempo ao SO de refletir o estado da tecla recém-pressionada.
            time.sleep(0.03)
            while self._engine.is_running() and self._hotkeys.is_pressed("toggle"):
                time.sleep(0.01)
            self._engine.stop()
            self._notifier.signal()

        self._hold_watch = threading.Thread(target=watch, name="HoldToClick", daemon=True)
        self._hold_watch.start()

    def _pick_point_at_cursor(self) -> None:
        """Atalho de captura: a posição atual do cursor vira o ponto fixo."""
        x, y = sendinput.get_cursor_pos()
        self._clear_errors()
        self._apply_config({"position_mode": "fixed", "fixed_x": int(x), "fixed_y": int(y)})

    def _toggle_macro_record_from_hotkey(self) -> None:
        combo = self._hotkeys.combo("macro_record")
        tokens = combo.tokens() if combo is not None else None
        if self._macro_recorder.is_recording():
            # As teclas do próprio atalho não entram na macro.
            self._macro_recorder.stop(strip_tokens=tokens)
            return
        self._clear_errors()
        self._stop_tier3_runners(keep_schedule=True)
        self._engine.stop()
        if not self._macro_recorder.start():
            self._fail("macro.recordFailed", "Não foi possível iniciar a gravação da macro.")

    def _cancel_wf_capture(self) -> None:
        timer, self._wf_capture_timer = self._wf_capture_timer, None
        self._wf_capture_until = None
        if timer is not None:
            timer.cancel()

    def _finish_wf_capture(self) -> None:
        self._wf_capture_timer = None
        self._wf_capture_until = None
        self._clear_errors()
        try:
            if foreground_is_own_window():
                raise ClickrError(
                    "filter.ownWindow",
                    "A janela em foco era o próprio Clickr. Troque para a janela desejada.",
                )
            try:
                process, title = self._engine.window_filter.foreground_info()
            except OSError as exc:
                raise ClickrError(
                    "filter.unavailable", f"Não foi possível ler a janela em foco: {exc}"
                ) from exc
            if not process and not title:
                raise ClickrError("filter.noWindow", "Nenhuma janela em foco foi encontrada.")
            self._apply_config(
                {
                    "window_filter": {
                        "enabled": True,
                        "process": process or "",
                        "title_contains": title or "",
                    }
                }
            )
        except ClickrError as exc:
            self._error = exc.to_dict()
        except Exception as exc:  # noqa: BLE001
            log.exception("Falha ao capturar a janela em foco")
            self._error = error_from_exception(exc)
        self._notifier.signal()

    def _key_guard(self) -> bool:
        """True quando as teclas iriam para a própria janela do Clickr."""
        native = foreground_is_own_window()
        return bool(native) if native is not None else False

    def _click_guard(self, x: int, y: int) -> bool:
        """True quando o clique cairia sobre uma janela do próprio Clickr."""
        native = point_in_own_window(x, y)
        if native is not None:
            return native
        window = self._window
        if window is None or not self._window_visible:
            return False
        try:
            wx, wy = int(window.x), int(window.y)
            ww, wh = int(window.width), int(window.height)
        except Exception:
            return False
        return wx <= x < wx + ww and wy <= y < wy + wh

    def _push_state(self) -> None:
        """Envia o estado atual para a UI (chamado só pela thread do UiNotifier)."""
        if not self._ui_alive:
            return
        window = self._window
        if window is None:
            return
        try:
            state = self.get_state()
            self._sync_tray(bool(state.get("running")))
            payload = json.dumps(state)
            window.evaluate_js(f"window.__clickrApplyState && window.__clickrApplyState({payload})")
        except Exception:
            # Janela em destruição ou webview ocupado: o próximo sinal reenvia.
            pass

    def _on_overlay_closed(self) -> None:
        if self._overlay is None and not self._picking:
            return
        self._overlay = None
        self._picking = False
        self._notifier.signal()

    def _close_overlay(self) -> None:
        overlay = self._overlay
        self._overlay = None
        if overlay is None:
            return
        try:
            overlay.destroy()
        except Exception:
            log.info("Overlay já estava fechado")

    def _close_info(self) -> None:
        info = self._info
        self._info = None
        if info is None:
            return
        try:
            info.destroy()
        except Exception:
            log.info("Janela de info já estava fechada")

    def _sync_tray(self, running: bool) -> None:
        """Reflete no ícone/menu da bandeja se algo está em execução."""
        if self._tray is None or running == self._tray_running:
            return
        self._tray_running = running
        try:
            self._tray.set_running(running)
        except Exception:
            log.exception("Falha ao atualizar a bandeja")

    def _tray_toggle(self) -> None:
        """Item Iniciar/Parar do menu da bandeja."""
        try:
            self._clear_errors()
            if self.get_state()["running"] or self._macro_recorder.is_recording():
                self._stop_everything()
            else:
                self._stop_tier3_runners(keep_schedule=True)
                self._engine.start()
        except Exception:
            log.exception("Falha ao alternar pela bandeja")
        self._notifier.signal()

    def _tray_show(self) -> None:
        window = self._window
        if window is None:
            return
        try:
            window.show()
            self._window_visible = True
            try:
                window.restore()
            except Exception:
                pass
        except Exception:
            log.exception("Falha ao mostrar a janela")

    def _tray_hide(self) -> None:
        window = self._window
        if window is None:
            return
        try:
            window.hide()
            self._window_visible = False
        except Exception:
            log.exception("Falha ao ocultar a janela")

    def _tray_quit(self) -> None:
        self._quit_requested = True
        window = self._window
        self.shutdown()
        if window is not None:
            try:
                window.destroy()
            except Exception:
                log.info("Janela principal já estava destruída")

    def _ui_string(self, dotted_key: str, default: str = "") -> str:
        """Lê chave pontilhada do catálogo do locale ativo; fallback pt-BR."""
        code = self._settings.get_locale() or "pt-BR"
        for locale in (code, "pt-BR"):
            path = locales_dir() / f"{locale}.json"
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, UnicodeError):
                continue
            cur: Any = data
            for part in dotted_key.split("."):
                if not isinstance(cur, dict) or part not in cur:
                    cur = None
                    break
                cur = cur[part]
            if isinstance(cur, str) and cur:
                return cur
        return default
