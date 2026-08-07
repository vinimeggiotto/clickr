"""AppController — ponte entre UI (pywebview JS API), motor, hotkeys, perfis e tray."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import webview

from app.paths import locales_dir, ui_dir
from app.settings import SUPPORTED_LOCALES, AppSettings
from app.tray import SystemTray
from core import sendinput
from core.engine import ClickEngine
from core.types import ClickConfig
from hotkeys.service import HotkeyService
from macros.player import MacroPlayer
from macros.recorder import MacroRecorder
from profiles.repo import ProfilesRepo
from scheduler.service import Scheduler
from scripts.runner import ScriptRunner

UI_DIR = ui_dir()


class AppController:
    """
    Expõe a API JS do pywebview e orquestra ClickEngine, HotkeyService,
    ProfilesRepo, SystemTray, macros, scheduler e scripts.
    """

    def __init__(self) -> None:
        self._engine = ClickEngine()
        self._hotkeys = HotkeyService(on_toggle=self._toggle_from_hotkey, hotkey="F6")
        self._profiles = ProfilesRepo()
        self._settings = AppSettings()
        self._macro_recorder = MacroRecorder()
        self._macro_player = MacroPlayer()
        self._scheduler = Scheduler()
        self._script = ScriptRunner()
        self._window: Any = None
        self._overlay: Any = None
        self._info: Any = None
        self._info_payload: dict[str, str] = {"title": "", "body_html": ""}
        self._tray: Optional[SystemTray] = None
        self._picking = False
        self._recording_hotkey = False
        self._quit_requested = False
        self._ui_alive = False

    def attach_window(self, window: Any) -> None:
        self._window = window

    def bootstrap_services(self) -> None:
        """Inicia hotkey global, bandeja e aplica always-on-top."""
        cfg = self._engine.get_config()
        self._hotkeys.set_hotkey(cfg.hotkey)
        self._hotkeys.start()
        self._apply_always_on_top(cfg.always_on_top)
        locale = self._settings.get_locale()
        self._tray = SystemTray(
            on_show=self._tray_show,
            on_hide=self._tray_hide,
            on_quit=self._tray_quit,
            locale=locale,
        )
        self._tray.start()
        self._engine.set_on_tick(self._notify_ui)
        self._macro_recorder.set_on_change(self._notify_ui)
        self._macro_player.set_on_tick(self._notify_ui)
        self._macro_player.set_on_done(self._notify_ui)
        self._scheduler.set_on_change(self._notify_ui)
        self._script.set_on_tick(self._notify_ui)
        self._script.set_on_done(self._notify_ui)
        self._ui_alive = True

    def shutdown(self) -> None:
        # Impede evaluate_js em WebView2 já descartado (ticks/hotkey em corrida com destroy).
        self._ui_alive = False
        self._clear_ui_callbacks()
        self._scheduler.cancel()
        self._macro_recorder.stop()
        self._macro_player.stop()
        self._script.stop()
        self._engine.stop()
        self._hotkeys.stop()
        if self._tray is not None:
            self._tray.stop()
            self._tray = None
        self._close_overlay()
        self._close_info()
        self._window = None

    def _clear_ui_callbacks(self) -> None:
        self._engine.set_on_tick(None)
        self._macro_recorder.set_on_change(None)
        self._macro_player.set_on_tick(None)
        self._macro_player.set_on_done(None)
        self._scheduler.set_on_change(None)
        self._script.set_on_tick(None)
        self._script.set_on_done(None)

    def should_close_to_tray(self) -> bool:
        """True se o fechamento da janela deve apenas ocultar (não encerrar)."""
        return not self._quit_requested

    # --- Bridge JS API -------------------------------------------------

    def start(self) -> dict[str, Any]:
        self._stop_tier3_runners(keep_schedule=True)
        self._engine.start()
        return self.get_state()

    def stop(self) -> dict[str, Any]:
        self._engine.stop()
        self._macro_player.stop()
        self._script.stop()
        return self.get_state()

    def get_state(self) -> dict[str, Any]:
        state = self._engine.get_state().to_dict()
        state["picking"] = self._picking
        state["recording_hotkey"] = self._recording_hotkey
        state["profiles"] = self._profiles.list_profiles()
        macro_err = self._macro_player.last_error()
        script_status = self._script.status()
        sched = self._scheduler.status()
        # Propaga erros de tier3 se o motor não tiver erro próprio
        if not state.get("last_error"):
            if macro_err:
                state["last_error"] = macro_err
            elif script_status.get("last_error"):
                state["last_error"] = script_status["last_error"]
            elif sched.get("last_error"):
                state["last_error"] = sched["last_error"]
        state["macro"] = {
            "recording": self._macro_recorder.is_recording(),
            "playing": self._macro_player.is_playing(),
            "event_count": self._macro_recorder.event_count(),
        }
        state["schedule"] = {
            "active": sched["active"],
            "at": sched["at"],
        }
        state["script"] = {
            "running": script_status["running"],
            "line": script_status["line"],
        }
        # Flags agregadas para UI (ativo se motor, macro ou script)
        if (
            self._macro_player.is_playing()
            or self._script.is_running()
            or self._macro_recorder.is_recording()
        ):
            state["running"] = (
                state["running"]
                or self._macro_player.is_playing()
                or self._script.is_running()
            )
        return state

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

        self._engine.set_last_error(None)
        updated = self._engine.update_config(data)
        self._sync_side_effects(updated, data)
        return self.get_state()

    def set_compact_mode(self, enabled: bool) -> dict[str, Any]:
        return self.set_config({"compact_mode": bool(enabled)})

    def pick_location(self) -> dict[str, Any]:
        """Abre overlay fullscreen para capturar XY (não bloqueia a bridge)."""
        if self._picking:
            return self.get_state()
        overlay_path = (UI_DIR / "overlay.html").resolve()
        if not overlay_path.is_file():
            raise FileNotFoundError(f"Overlay não encontrado: {overlay_path}")

        self._close_overlay()
        self._picking = True
        vx, vy, vw, vh = sendinput.get_virtual_screen_rect()
        # Uma janela cobrindo a tela virtual (todos os monitores), não fullscreen de 1 tela.
        self._overlay = webview.create_window(
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
            background_color="#000000",
        )
        self._notify_ui()
        return self.get_state()

    def confirm_pick(self, x: int = 0, y: int = 0) -> dict[str, Any]:
        """Callback do overlay: usa posição real do cursor e fecha a captura."""
        cx, cy = sendinput.get_cursor_pos()
        self._picking = False
        self._close_overlay()
        self._engine.update_config(
            {
                "position_mode": "fixed",
                "fixed_x": int(cx),
                "fixed_y": int(cy),
            }
        )
        self._notify_ui()
        return self.get_state()

    def cancel_pick(self) -> dict[str, Any]:
        self._picking = False
        self._close_overlay()
        self._notify_ui()
        return self.get_state()

    def add_sequence_point(self, x: Optional[int] = None, y: Optional[int] = None, delay_ms: int = 0) -> dict[str, Any]:
        """Adiciona um passo à sequência (XY atuais do cursor se omitidos)."""
        if x is None or y is None:
            cx, cy = sendinput.get_cursor_pos()
            x = cx if x is None else int(x)
            y = cy if y is None else int(y)
        cfg = self._engine.get_config()
        steps = [s.to_dict() for s in cfg.sequence]
        steps.append({"x": int(x), "y": int(y), "delay_ms": max(0, int(delay_ms or 0))})
        self._engine.update_config({"sequence": steps})
        return self.get_state()

    def remove_sequence_point(self, index: int) -> dict[str, Any]:
        cfg = self._engine.get_config()
        steps = [s.to_dict() for s in cfg.sequence]
        idx = int(index)
        if idx < 0 or idx >= len(steps):
            raise IndexError("Índice de sequência inválido")
        steps.pop(idx)
        self._engine.update_config({"sequence": steps})
        return self.get_state()

    def clear_sequence(self) -> dict[str, Any]:
        self._engine.update_config({"sequence": []})
        return self.get_state()

    def record_hotkey(self) -> dict[str, Any]:
        """Inicia gravação da próxima tecla como hotkey de start/stop."""
        if self._recording_hotkey:
            return self.get_state()
        self._recording_hotkey = True
        self._engine.set_last_error(None)
        self._hotkeys.begin_capture(self._on_hotkey_captured)
        self._notify_ui()
        return self.get_state()

    def cancel_record_hotkey(self) -> dict[str, Any]:
        self._hotkeys.cancel_capture()
        self._recording_hotkey = False
        self._notify_ui()
        return self.get_state()

    # --- Macro ---------------------------------------------------------

    def macro_record_start(self) -> dict[str, Any]:
        if self._macro_recorder.is_recording():
            return self.get_state()
        self._stop_tier3_runners(keep_schedule=True)
        self._engine.stop()
        self._engine.set_last_error(None)
        ok = self._macro_recorder.start()
        if not ok:
            self._engine.set_last_error("Não foi possível iniciar a gravação da macro.")
        return self.get_state()

    def macro_record_stop(self) -> dict[str, Any]:
        events = self._macro_recorder.stop()
        state = self.get_state()
        state["macro"]["event_count"] = len(events)
        return state

    def macro_play(self) -> dict[str, Any]:
        if self._macro_player.is_playing():
            return self.get_state()
        events = self._macro_recorder.get_events()
        self._engine.stop()
        self._script.stop()
        self._engine.set_last_error(None)
        ok = self._macro_player.play(events)
        if not ok:
            err = self._macro_player.last_error() or "Falha ao reproduzir macro."
            self._engine.set_last_error(err)
        return self.get_state()

    def macro_stop(self) -> dict[str, Any]:
        if self._macro_recorder.is_recording():
            self._macro_recorder.stop()
        self._macro_player.stop()
        return self.get_state()

    def macro_clear(self) -> dict[str, Any]:
        if self._macro_recorder.is_recording() or self._macro_player.is_playing():
            self._engine.set_last_error("Pare a macro antes de limpar.")
            return self.get_state()
        self._macro_recorder.clear()
        return self.get_state()

    # --- Scheduler -----------------------------------------------------

    def schedule_set(self, when: str) -> dict[str, Any]:
        """Agenda início do motor. when: ISO local 'YYYY-MM-DDTHH:MM' ou com segundos."""
        raw = (when or "").strip()
        if not raw:
            self._engine.set_last_error("Informe data e hora para agendar.")
            return self.get_state()
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            self._engine.set_last_error("Data/hora inválida. Use AAAA-MM-DDTHH:MM.")
            return self.get_state()
        try:
            self._scheduler.schedule(dt, self._on_schedule_fire)
            self._engine.set_last_error(None)
        except ValueError as exc:
            self._engine.set_last_error(str(exc))
        return self.get_state()

    def schedule_cancel(self) -> dict[str, Any]:
        self._scheduler.cancel()
        return self.get_state()

    # --- Script --------------------------------------------------------

    def script_run(self, source: str = "") -> dict[str, Any]:
        if self._script.is_running():
            return self.get_state()
        self._engine.stop()
        self._macro_player.stop()
        if self._macro_recorder.is_recording():
            self._macro_recorder.stop()
        self._engine.set_last_error(None)
        ok = self._script.run(source or "")
        if not ok:
            err = self._script.last_error() or "Falha ao executar script."
            self._engine.set_last_error(err)
        return self.get_state()

    def script_stop(self) -> dict[str, Any]:
        self._script.stop()
        return self.get_state()

    def list_profiles(self) -> list[str]:
        return self._profiles.list_profiles()

    def save_profile(self, name: str) -> dict[str, Any]:
        cfg = self._engine.get_config().to_dict()
        saved = self._profiles.save(name, cfg)
        state = self.get_state()
        state["saved_profile"] = saved
        return state

    def load_profile(self, name: str) -> dict[str, Any]:
        data = self._profiles.load(name)
        self._engine.set_last_error(None)
        updated = self._engine.update_config(data)
        self._sync_side_effects(updated, data)
        return self.get_state()

    def export_profile(self, name: str = "") -> dict[str, Any]:
        """Abre diálogo Salvar e exporta perfil (salvo ou config atual) em JSON."""
        label = (name or "").strip() or "clickr-perfil"
        try:
            safe_name = ProfilesRepo._validate_name(label)
        except ValueError as exc:
            self._engine.set_last_error(str(exc))
            return self.get_state()

        result = webview.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=f"{safe_name}.json",
            file_types=("Arquivos JSON (*.json)",),
        )
        if not result:
            return self.get_state()
        dest = Path(result[0] if isinstance(result, (list, tuple)) else result)
        try:
            cfg = self._engine.get_config().to_dict()
            if self._profiles.exists(safe_name):
                self._profiles.export_to(safe_name, dest)
            else:
                self._profiles.export_config(safe_name, cfg, dest)
            self._engine.set_last_error(None)
            state = self.get_state()
            state["exported_path"] = str(dest)
            return state
        except (OSError, ValueError, FileNotFoundError) as exc:
            self._engine.set_last_error(str(exc))
            return self.get_state()

    def import_profile(self, name: str = "") -> dict[str, Any]:
        """Abre diálogo Abrir e importa JSON para a pasta de perfis."""
        result = webview.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("Arquivos JSON (*.json)",),
        )
        if not result:
            return self.get_state()
        src = Path(result[0] if isinstance(result, (list, tuple)) else result)
        override = (name or "").strip() or None
        try:
            saved = self._profiles.import_from(src, name=override)
            data = self._profiles.load(saved)
            self._engine.set_last_error(None)
            updated = self._engine.update_config(data)
            self._sync_side_effects(updated, data)
            state = self.get_state()
            state["imported_profile"] = saved
            return state
        except (OSError, ValueError, FileNotFoundError, TypeError) as exc:
            self._engine.set_last_error(str(exc))
            return self.get_state()

    def set_always_on_top(self, enabled: bool) -> dict[str, Any]:
        return self.set_config({"always_on_top": bool(enabled)})

    def show_window(self) -> None:
        self._tray_show()

    def hide_window(self, notify: bool = False) -> None:
        """Oculta a janela. Se notify=True, avisa que o app segue na bandeja."""
        if notify and self._tray is not None:
            self._tray.notify_still_running()
        self._tray_hide()

    def get_settings(self) -> dict[str, Any]:
        """Preferências do app (locale). Não inclui presets de clique."""
        data = self._settings.load()
        return {
            "locale": data.get("locale"),
            "supported_locales": list(SUPPORTED_LOCALES),
        }

    def set_locale(self, code: str) -> dict[str, Any]:
        """Persiste locale, atualiza menu da bandeja e devolve settings."""
        saved = self._settings.set_locale(str(code or "").strip())
        if self._tray is not None and saved.get("locale"):
            self._tray.set_locale(str(saved["locale"]))
        return {
            "locale": saved.get("locale"),
            "supported_locales": list(SUPPORTED_LOCALES),
        }

    def window_minimize(self) -> None:
        """Minimiza a janela principal (title bar custom)."""
        if self._window is None:
            raise RuntimeError("Janela não anexada")
        self._window.minimize()

    def window_close(self) -> None:
        """Fecha para a bandeja e notifica o usuário."""
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
                x = int(main.x) + int(main.width) + 16
                y = int(main.y)
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

    def _stop_tier3_runners(self, keep_schedule: bool = False) -> None:
        if self._macro_recorder.is_recording():
            self._macro_recorder.stop()
        self._macro_player.stop()
        self._script.stop()
        if not keep_schedule:
            self._scheduler.cancel()

    def _on_schedule_fire(self) -> None:
        self._stop_tier3_runners(keep_schedule=True)
        self._engine.start()
        self._notify_ui()

    def _sync_side_effects(self, config: ClickConfig, changed: dict[str, Any]) -> None:
        if "hotkey" in changed and changed["hotkey"] is not None:
            name = self._hotkeys.set_hotkey(str(changed["hotkey"]))
            if name != config.hotkey:
                self._engine.update_config({"hotkey": name})
        if "always_on_top" in changed:
            self._apply_always_on_top(bool(config.always_on_top))

    def _apply_always_on_top(self, enabled: bool) -> None:
        window = self._window
        if window is None:
            return
        try:
            window.on_top = bool(enabled)
        except Exception as exc:
            self._engine.set_last_error(f"Falha ao aplicar always-on-top: {exc}")

    def _on_hotkey_captured(self, name: str) -> None:
        self._recording_hotkey = False
        try:
            resolved = self._hotkeys.set_hotkey(name)
            self._engine.update_config({"hotkey": resolved})
            self._engine.set_last_error(None)
        except ValueError as exc:
            self._engine.set_last_error(str(exc))
        self._notify_ui()

    def _toggle_from_hotkey(self) -> None:
        if self._picking or self._recording_hotkey:
            return
        if self._macro_recorder.is_recording():
            return
        if self._macro_player.is_playing():
            self._macro_player.stop()
            self._notify_ui()
            return
        if self._script.is_running():
            self._script.stop()
            self._notify_ui()
            return
        self._engine.toggle()
        self._notify_ui()

    def _notify_ui(self) -> None:
        if not self._ui_alive:
            return
        window = self._window
        if window is None:
            return
        try:
            window.evaluate_js("window.__clickrApplyState && window.__clickrApplyState()")
        except Exception:
            pass

    def _close_overlay(self) -> None:
        overlay = self._overlay
        self._overlay = None
        if overlay is None:
            return
        try:
            overlay.destroy()
        except Exception:
            pass

    def _close_info(self) -> None:
        info = self._info
        self._info = None
        if info is None:
            return
        try:
            info.destroy()
        except Exception:
            pass

    def _tray_show(self) -> None:
        window = self._window
        if window is None:
            return
        try:
            window.show()
        except Exception:
            pass

    def _tray_hide(self) -> None:
        window = self._window
        if window is None:
            return
        try:
            window.hide()
        except Exception:
            pass

    def _tray_quit(self) -> None:
        self._quit_requested = True
        window = self._window
        self.shutdown()
        if window is not None:
            try:
                window.destroy()
            except Exception:
                pass

    def default_config(self) -> ClickConfig:
        return self._engine.get_config()

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
