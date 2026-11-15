"""Bandeja do sistema (pystray) — mostrar/ocultar e sair."""

from __future__ import annotations

import json
import sys
import threading
from typing import Callable, Optional

import pystray
from PIL import Image

from app.paths import assets_dir, locales_dir
from app.settings import SUPPORTED_LOCALES

ICON_PATH = assets_dir() / "icon.png"
FALLBACK_LOCALE = "pt-BR"


class SystemTray:
    """Ícone na bandeja com menu: Mostrar, Ocultar, Sair (rótulos via locale)."""

    def __init__(
        self,
        on_show: Callable[[], None],
        on_hide: Callable[[], None],
        on_quit: Callable[[], None],
        locale: str | None = None,
    ) -> None:
        self._on_show = on_show
        self._on_hide = on_hide
        self._on_quit = on_quit
        self._locale = locale if locale in SUPPORTED_LOCALES else FALLBACK_LOCALE
        self._labels = self._load_labels(self._locale)
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def start(self, detached: bool = False) -> None:
        """
        Inicia o ícone. No macOS o pystray precisa ser iniciado na thread
        principal com run_detached (antes do loop do pywebview); nos demais SOs
        roda em thread própria.
        """
        if self._icon is not None:
            return
        image = self._load_icon()
        self._icon = pystray.Icon("Clickr", image, "Clickr", self._build_menu())
        if detached or sys.platform == "darwin":
            self._icon.run_detached()
            return
        self._thread = threading.Thread(target=self._icon.run, name="SystemTray", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        icon = self._icon
        self._icon = None
        if icon is not None:
            icon.stop()

    def set_locale(self, code: str) -> None:
        """Recarrega rótulos do menu a partir do catálogo do locale."""
        if code not in SUPPORTED_LOCALES:
            raise ValueError(f"Locale não suportado: {code}")
        self._locale = code
        self._labels = self._load_labels(code)
        icon = self._icon
        if icon is None:
            return
        icon.menu = self._build_menu()
        try:
            icon.update_menu()
        except Exception:
            pass

    def notify(self, message: str, title: str = "Clickr") -> None:
        """Balloon/toast do Windows via ícone da bandeja."""
        icon = self._icon
        if icon is None:
            return
        if not getattr(icon, "HAS_NOTIFICATION", True):
            return
        icon.notify(message, title)

    def notify_still_running(self) -> None:
        """Toast padrão ao minimizar para a bandeja, já traduzido."""
        self.notify(
            self._labels.get("notifyBody", ""),
            self._labels.get("notifyTitle", "Clickr"),
        )

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(self._labels.get("show", "Mostrar"), self._handle_show, default=True),
            pystray.MenuItem(self._labels.get("hide", "Ocultar"), self._handle_hide),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(self._labels.get("quit", "Sair"), self._handle_quit),
        )

    def _handle_show(self, icon: object = None, item: object = None) -> None:
        self._on_show()

    def _handle_hide(self, icon: object = None, item: object = None) -> None:
        self._on_hide()

    def _handle_quit(self, icon: object = None, item: object = None) -> None:
        self._on_quit()

    @staticmethod
    def _load_icon() -> Image.Image:
        if ICON_PATH.is_file():
            try:
                return Image.open(ICON_PATH).convert("RGBA")
            except OSError:
                pass
        # Ícone ausente/corrompido não pode impedir a bandeja: desenha um substituto.
        from PIL import ImageDraw

        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        ImageDraw.Draw(image).ellipse((6, 6, 58, 58), fill=(242, 163, 59, 255))
        return image

    @staticmethod
    def _load_labels(code: str) -> dict[str, str]:
        """Lê chaves tray.* do JSON; fallback pt-BR só para chave ausente."""
        fallback = SystemTray._read_tray_section(FALLBACK_LOCALE)
        if code == FALLBACK_LOCALE:
            return fallback
        primary = SystemTray._read_tray_section(code)
        merged = dict(fallback)
        merged.update({k: v for k, v in primary.items() if isinstance(v, str) and v})
        return merged

    @staticmethod
    def _read_tray_section(code: str) -> dict[str, str]:
        path = locales_dir() / f"{code}.json"
        if not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            return {}
        tray = data.get("tray") if isinstance(data, dict) else None
        if not isinstance(tray, dict):
            return {}
        out: dict[str, str] = {}
        for key in ("show", "hide", "quit", "notifyTitle", "notifyBody"):
            val = tray.get(key)
            if isinstance(val, str):
                out[key] = val
        return out
