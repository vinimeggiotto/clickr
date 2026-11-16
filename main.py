"""Clickr — entrypoint."""

from __future__ import annotations

import sys


def main() -> int:
    from app.log import arm_startup_watchdog, setup_logging

    log = setup_logging()
    arm_startup_watchdog()

    from core.dpi import enable_dpi_awareness

    try:
        enable_dpi_awareness()
    except OSError:
        log.exception("Falha ao ativar DPI awareness")

    try:
        from app.autostart import MINIMIZED_FLAG
        from app.bootstrap import run

        run(start_minimized=MINIMIZED_FLAG in sys.argv[1:])
    except Exception:
        log.exception("Erro fatal")
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
