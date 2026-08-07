"""Bootstrap da janela pywebview e ciclo de vida do Clickr."""

from __future__ import annotations

import sys

import webview

from app.controller import AppController
from app.paths import ui_dir

UI_DIR = ui_dir()
# Largura: conteúdo ~340 + rail lateral ~96 + paddings
WINDOW_WIDTH = 468
# Conteúdo ~640 + titlebar custom (~36)
WINDOW_HEIGHT = 676


def create_app() -> tuple[webview.Window, AppController]:
    if sys.platform != "win32":
        raise RuntimeError("Clickr é suportado apenas no Windows.")

    controller = AppController()
    index = (UI_DIR / "index.html").resolve()
    if not index.is_file():
        raise FileNotFoundError(f"UI não encontrada: {index}")

    window = webview.create_window(
        title="Clickr",
        url=index.as_uri(),
        js_api=controller,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        resizable=False,
        on_top=True,
        frameless=True,
        easy_drag=False,
        background_color="#14100c",
    )
    controller.attach_window(window)
    return window, controller


def run() -> None:
    window, controller = create_app()

    def on_start() -> None:
        controller.bootstrap_services()

    def on_closing() -> bool:
        # Oculta na bandeja em vez de encerrar (Sair vem do tray).
        if controller.should_close_to_tray():
            controller.hide_window(notify=True)
            return False
        return True

    def on_closed() -> None:
        controller.shutdown()

    window.events.closing += on_closing
    window.events.closed += on_closed
    webview.start(on_start, debug=False)
