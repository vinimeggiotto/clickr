"""DPI awareness do processo (multi-monitor / coordenadas corretas)."""

from __future__ import annotations

import ctypes
import sys

# DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
_DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)

# Já aplicado neste processo (chamada idempotente).
_ERROR_ACCESS_DENIED = 5


def enable_dpi_awareness() -> None:
    """
    Chama SetProcessDpiAwarenessContext(PER_MONITOR_AWARE_V2) no startup.

    Deve rodar antes de criar janelas / ler coordenadas de tela.
    Se o contexto já estiver definido (erro 5), a chamada é considerada concluída.
    """
    if sys.platform != "win32":
        return
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    set_ctx = getattr(user32, "SetProcessDpiAwarenessContext", None)
    if set_ctx is None:
        raise OSError("SetProcessDpiAwarenessContext indisponível neste Windows")
    set_ctx.argtypes = (ctypes.c_void_p,)
    set_ctx.restype = ctypes.c_bool
    ctypes.set_last_error(0)
    ok = set_ctx(_DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
    if ok:
        return
    err = ctypes.get_last_error()
    if err == _ERROR_ACCESS_DENIED:
        return
    raise OSError(f"SetProcessDpiAwarenessContext falhou, erro Win32={err}")
