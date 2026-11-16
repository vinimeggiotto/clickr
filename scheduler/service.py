"""Scheduler — dispara uma ação em data/hora local, uma vez ou de forma recorrente."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from core.errors import ClickrError, error_from_exception

REPEATS = ("once", "daily", "interval")
TARGETS = ("engine", "macro", "script", "profile")
MIN_INTERVAL_S = 5
MAX_INTERVAL_S = 7 * 24 * 3600


def normalize_schedule(data: Any) -> dict[str, Any]:
    """Valida um agendamento ({at, repeat, interval_s, target, profile})."""
    if not isinstance(data, dict):
        raise ClickrError("schedule.invalid", "Agendamento inválido.")
    raw_at = data.get("at")
    if isinstance(raw_at, datetime):
        at = raw_at
    else:
        text = str(raw_at or "").strip()
        if not text:
            raise ClickrError("schedule.empty", "Informe data e hora para agendar.")
        try:
            at = datetime.fromisoformat(text)
        except ValueError:
            raise ClickrError(
                "schedule.invalid", "Data/hora inválida. Use AAAA-MM-DDTHH:MM."
            ) from None
    if at.tzinfo is not None:
        raise ClickrError("schedule.invalid", "Use data/hora local sem timezone (naive).")
    repeat = data.get("repeat") or "once"
    if repeat not in REPEATS:
        raise ClickrError("schedule.invalid", "Tipo de repetição inválido.")
    target = data.get("target") or "engine"
    if target not in TARGETS:
        raise ClickrError("schedule.invalid", "Alvo de agendamento inválido.")
    interval_s = 0
    if repeat == "interval":
        try:
            interval_s = int(data.get("interval_s") or 0)
        except (TypeError, ValueError):
            interval_s = 0
        if not MIN_INTERVAL_S <= interval_s <= MAX_INTERVAL_S:
            raise ClickrError(
                "schedule.badInterval",
                f"O intervalo deve ficar entre {MIN_INTERVAL_S} s e 7 dias.",
                min=MIN_INTERVAL_S,
            )
    profile = str(data.get("profile") or "").strip() if target == "profile" else ""
    if target == "profile" and not profile:
        raise ClickrError("schedule.needProfile", "Escolha o perfil a ser iniciado.")
    return {
        "at": at.replace(microsecond=0),
        "repeat": repeat,
        "interval_s": interval_s,
        "target": target,
        "profile": profile,
    }


class Scheduler:
    """
    Mantém no máximo um agendamento ativo.

    Uma thread confere o relógio de parede a cada segundo (em vez de um timer
    único), então o disparo continua correto depois de suspender/retomar o
    computador ou de o relógio ser ajustado. Sem retry: erro do callback fica
    em last_error.
    """

    def __init__(self, now: Callable[[], datetime] = datetime.now) -> None:
        self._now = now
        self._lock = threading.Lock()
        self._schedule: Optional[dict[str, Any]] = None
        self._on_fire: Optional[Callable[[dict[str, Any]], None]] = None
        self._on_change: Optional[Callable[[], None]] = None
        self._last_error: Optional[dict[str, Any]] = None
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def set_on_change(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_change = callback

    def set_on_fire(self, callback: Optional[Callable[[dict[str, Any]], None]]) -> None:
        self._on_fire = callback

    # --- API ------------------------------------------------------------

    def schedule(self, when: Any, on_fire: Any = None, **options: Any) -> dict[str, Any]:
        """
        Agenda um disparo. `when` é datetime/ISO local; options: repeat,
        interval_s, target, profile. Para "once" e "interval" o horário precisa
        estar no futuro; "daily" com horário passado vale a partir de amanhã.
        """
        data = normalize_schedule({"at": when, **options})
        now = self._now()
        if data["at"] <= now:
            if data["repeat"] == "daily":
                data["at"] = self._roll_daily(data["at"], now)
            else:
                raise ClickrError("schedule.past", "Horário de agendamento deve ser no futuro.")
        if on_fire is not None:
            self._on_fire = on_fire
        with self._lock:
            self._schedule = data
            self._last_error = None
        self._ensure_thread()
        self._wake.set()
        self._notify()
        return self.to_dict() or {}

    def restore(self, data: Any) -> bool:
        """
        Reativa um agendamento salvo. Um disparo único já vencido é descartado;
        os recorrentes avançam para a próxima ocorrência. Retorna True se ativo.
        """
        try:
            item = normalize_schedule(data)
        except ClickrError:
            return False
        now = self._now()
        if item["at"] <= now:
            if item["repeat"] == "once":
                return False
            if item["repeat"] == "daily":
                item["at"] = self._roll_daily(item["at"], now)
            else:
                item["at"] = (now + timedelta(seconds=item["interval_s"])).replace(microsecond=0)
        with self._lock:
            self._schedule = item
        self._ensure_thread()
        self._wake.set()
        self._notify()
        return True

    def cancel(self) -> bool:
        with self._lock:
            had = self._schedule is not None
            self._schedule = None
        self._wake.set()
        if had:
            self._notify()
        return had

    def shutdown(self) -> None:
        self._stop.set()
        self._wake.set()

    def is_active(self) -> bool:
        with self._lock:
            return self._schedule is not None

    def scheduled_at(self) -> Optional[datetime]:
        with self._lock:
            return self._schedule["at"] if self._schedule else None

    def last_error(self) -> Optional[dict[str, Any]]:
        with self._lock:
            return self._last_error

    def clear_error(self) -> None:
        with self._lock:
            self._last_error = None

    def to_dict(self) -> Optional[dict[str, Any]]:
        """Forma serializável do agendamento ativo (para settings.json)."""
        with self._lock:
            if self._schedule is None:
                return None
            item = dict(self._schedule)
        item["at"] = item["at"].isoformat(timespec="seconds")
        return item

    def status(self) -> dict[str, Any]:
        item = self.to_dict()
        with self._lock:
            error = self._last_error
        return {
            "active": item is not None,
            "at": item["at"] if item else None,
            "repeat": item["repeat"] if item else "once",
            "interval_s": item["interval_s"] if item else 0,
            "target": item["target"] if item else "engine",
            "profile": item["profile"] if item else "",
            "last_error": error,
        }

    # --- Interno --------------------------------------------------------

    @staticmethod
    def _roll_daily(at: datetime, now: datetime) -> datetime:
        candidate = now.replace(
            hour=at.hour, minute=at.minute, second=at.second, microsecond=0
        )
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    def _ensure_thread(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="Scheduler", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            due: Optional[dict[str, Any]] = None
            with self._lock:
                item = self._schedule
                wait = 1.0
                if item is not None:
                    now = self._now()
                    remaining = (item["at"] - now).total_seconds()
                    if remaining <= 0:
                        due = dict(item)
                        if item["repeat"] == "daily":
                            item["at"] = self._roll_daily(item["at"], now)
                        elif item["repeat"] == "interval":
                            item["at"] = (
                                now + timedelta(seconds=item["interval_s"])
                            ).replace(microsecond=0)
                        else:
                            self._schedule = None
                    else:
                        wait = min(1.0, max(0.02, remaining))
            if due is not None:
                self._fire(due)
                continue
            self._wake.wait(timeout=wait)
            self._wake.clear()

    def _fire(self, item: dict[str, Any]) -> None:
        callback = self._on_fire
        try:
            if callback is not None:
                payload = dict(item)
                payload["at"] = item["at"].isoformat(timespec="seconds")
                callback(payload)
        except Exception as exc:
            with self._lock:
                self._last_error = error_from_exception(exc)
        self._notify()

    def _notify(self) -> None:
        cb = self._on_change
        if cb is not None:
            try:
                cb()
            except Exception:
                pass
