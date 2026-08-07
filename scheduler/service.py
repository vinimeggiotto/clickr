"""Scheduler — agenda início em data/hora local."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Callable, Optional


class Scheduler:
    """
    Dispara um callback uma vez em um datetime local.

    Integração: AppController passa start do motor como on_fire.
    Sem retry: se o callback falhar, o erro fica em last_error.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._when: Optional[datetime] = None
        self._on_fire: Optional[Callable[[], None]] = None
        self._on_change: Optional[Callable[[], None]] = None
        self._last_error: Optional[str] = None

    def set_on_change(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_change = callback

    def schedule(self, when: datetime, on_fire: Callable[[], None]) -> None:
        """Agenda disparo único. when deve ser timezone-naive local no futuro."""
        if when.tzinfo is not None:
            raise ValueError("Use data/hora local sem timezone (naive).")
        now = datetime.now()
        delay = (when - now).total_seconds()
        if delay <= 0:
            raise ValueError("Horário de agendamento deve ser no futuro.")

        with self._lock:
            self._cancel_locked()
            self._when = when
            self._on_fire = on_fire
            self._last_error = None
            self._timer = threading.Timer(delay, self._fire)
            self._timer.daemon = True
            self._timer.start()
        self._notify()

    def cancel(self) -> bool:
        with self._lock:
            had = self._timer is not None or self._when is not None
            self._cancel_locked()
        if had:
            self._notify()
        return had

    def is_active(self) -> bool:
        with self._lock:
            return self._timer is not None and self._when is not None

    def scheduled_at(self) -> Optional[datetime]:
        with self._lock:
            return self._when

    def last_error(self) -> Optional[str]:
        with self._lock:
            return self._last_error

    def status(self) -> dict[str, Any]:
        with self._lock:
            when = self._when
            return {
                "active": self._timer is not None and when is not None,
                "at": when.isoformat(timespec="seconds") if when is not None else None,
                "last_error": self._last_error,
            }

    def _cancel_locked(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self._when = None
        self._on_fire = None

    def _fire(self) -> None:
        with self._lock:
            callback = self._on_fire
            self._timer = None
            self._when = None
            self._on_fire = None
        try:
            if callback is not None:
                callback()
        except Exception as exc:
            with self._lock:
                self._last_error = str(exc)
        self._notify()

    def _notify(self) -> None:
        cb = self._on_change
        if cb is not None:
            cb()
