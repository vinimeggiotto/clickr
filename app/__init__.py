"""Camada de aplicação do Clickr (bootstrap e controller).

O controller é importado sob demanda para que módulos leves (paths, settings,
log) possam ser usados sem carregar pywebview.
"""

__all__ = ["AppController"]


def __getattr__(name: str):
    if name == "AppController":
        from app.controller import AppController

        return AppController
    raise AttributeError(name)
