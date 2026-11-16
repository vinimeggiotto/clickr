"""Serviço de hotkeys globais do Clickr."""

__all__ = ["HotkeyService"]


def __getattr__(name: str):
    if name == "HotkeyService":
        from hotkeys.service import HotkeyService

        return HotkeyService
    raise AttributeError(name)
