"""Clickr — entrypoint."""

from __future__ import annotations

import sys


def main() -> int:
    from core.dpi import enable_dpi_awareness

    enable_dpi_awareness()

    from app.bootstrap import run

    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
