"""Bootstrap da janela pywebview e ciclo de vida do Clickr."""

from __future__ import annotations

import sys

import webview

from app.controller import AppController
from app.log import get_logger
from app.paths import ui_dir
from app.single_instance import SingleInstance

log = get_logger()

UI_DIR = ui_dir()
# Largura: conteúdo ~340 + rail lateral ~96 + paddings
WINDOW_WIDTH = 468
# Conteúdo ~640 + titlebar custom (~36)
WINDOW_HEIGHT = 676


def create_app(start_minimized: bool = False) -> tuple[webview.Window, AppController]:
    controller = AppController()
    index = (UI_DIR / "index.html").resolve()
    if not index.is_file():
        raise FileNotFoundError(f"UI não encontrada: {index}")

    position = controller.initial_window_pos()
    window = webview.create_window(
        title="Clickr",
        url=index.as_uri(),
        js_api=controller,
        x=position[0] if position else None,
        y=position[1] if position else None,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        resizable=False,
        on_top=True,
        frameless=True,
        easy_drag=False,
        background_color="#14100c",
        hidden=bool(start_minimized),
    )
    controller.attach_window(window)
    if start_minimized:
        controller.mark_window_hidden()
    return window, controller


def run(start_minimized: bool = False) -> None:
    instance = SingleInstance()
    if not instance.acquire():
        # Já existe um Clickr aberto: pede que ele apareça e encerra este.
        instance.request_show()
        log.info("Outra instância em execução; encerrando esta.")
        return

    window, controller = create_app(start_minimized=start_minimized)
    instance.watch(controller.show_window)

    def on_start() -> None:
        try:
            controller.bootstrap_services()
        except Exception:
            log.exception("Falha ao iniciar serviços")
        # Iniciado minimizado sem bandeja = app inalcançável: mostra a janela.
        if start_minimized and not controller.has_tray():
            controller.show_window()

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
    if sys.platform == "darwin":
        # pystray no macOS exige a thread principal, antes do loop do pywebview.
        controller.start_tray(detached=True)
    try:
        webview.start(on_start, debug=False)
    finally:
        instance.release()
