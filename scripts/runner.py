"""ScriptRunner — DSL mínima: click, move, wait, key, loops limitados."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

from core import sendinput
from core.sendinput import ButtonName

MAX_LINES = 500
MAX_LOOP_COUNT = 1000
MAX_LOOP_DEPTH = 2

_VALID_BUTTONS = frozenset({"left", "right", "middle", "x1", "x2"})


@dataclass(frozen=True)
class CmdClick:
    button: ButtonName
    x: Optional[int] = None
    y: Optional[int] = None


@dataclass(frozen=True)
class CmdMove:
    x: int
    y: int


@dataclass(frozen=True)
class CmdWait:
    ms: int


@dataclass(frozen=True)
class CmdKey:
    key: str


@dataclass(frozen=True)
class CmdLoop:
    count: int
    body: tuple[Any, ...]


Command = Union[CmdClick, CmdMove, CmdWait, CmdKey, CmdLoop]


def parse_script(source: str) -> list[Command]:
    """
    Analisa DSL linha a linha.

    Gramática (por linha):
      click [button] [x y]
      move x y
      wait ms
      key NAME
      loop N
      ...comandos indentados ou até end
      end
      # comentário
    """
    if source is None:
        raise ValueError("Script vazio")
    raw_lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if len(raw_lines) > MAX_LINES:
        raise ValueError(f"Script excede {MAX_LINES} linhas")

    lines: list[tuple[int, str]] = []
    for i, line in enumerate(raw_lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append((i, stripped))

    commands, idx = _parse_block(lines, 0, depth=0)
    if idx < len(lines):
        line_no, text = lines[idx]
        raise ValueError(f"Linha {line_no}: token inesperado '{text}'")
    return commands


def _parse_block(
    lines: list[tuple[int, str]], start: int, depth: int
) -> tuple[list[Command], int]:
    commands: list[Command] = []
    i = start
    while i < len(lines):
        line_no, text = lines[i]
        parts = text.split()
        op = parts[0].lower()

        if op == "end":
            if depth == 0:
                raise ValueError(f"Linha {line_no}: 'end' sem loop correspondente")
            return commands, i + 1

        if op == "loop":
            if depth >= MAX_LOOP_DEPTH:
                raise ValueError(f"Linha {line_no}: profundidade de loop > {MAX_LOOP_DEPTH}")
            if len(parts) != 2:
                raise ValueError(f"Linha {line_no}: use 'loop N'")
            try:
                count = int(parts[1])
            except ValueError as exc:
                raise ValueError(f"Linha {line_no}: contagem de loop inválida") from exc
            if count < 1 or count > MAX_LOOP_COUNT:
                raise ValueError(
                    f"Linha {line_no}: loop deve ser entre 1 e {MAX_LOOP_COUNT}"
                )
            body, next_i = _parse_block(lines, i + 1, depth + 1)
            commands.append(CmdLoop(count=count, body=tuple(body)))
            i = next_i
            continue

        if op == "click":
            commands.append(_parse_click(line_no, parts))
            i += 1
            continue
        if op == "move":
            if len(parts) != 3:
                raise ValueError(f"Linha {line_no}: use 'move X Y'")
            commands.append(CmdMove(x=int(parts[1]), y=int(parts[2])))
            i += 1
            continue
        if op == "wait":
            if len(parts) != 2:
                raise ValueError(f"Linha {line_no}: use 'wait MS'")
            ms = int(parts[1])
            if ms < 0:
                raise ValueError(f"Linha {line_no}: wait não pode ser negativo")
            commands.append(CmdWait(ms=ms))
            i += 1
            continue
        if op == "key":
            if len(parts) != 2:
                raise ValueError(f"Linha {line_no}: use 'key NOME'")
            key = parts[1].upper()
            sendinput.name_to_vk(key)  # valida
            commands.append(CmdKey(key=key))
            i += 1
            continue

        raise ValueError(f"Linha {line_no}: comando desconhecido '{op}'")

    if depth > 0:
        raise ValueError("loop sem 'end'")
    return commands, i


def _parse_click(line_no: int, parts: list[str]) -> CmdClick:
    # click
    # click left
    # click 100 200
    # click left 100 200
    if len(parts) == 1:
        return CmdClick(button="left")
    if len(parts) == 2:
        token = parts[1].lower()
        if token in _VALID_BUTTONS:
            return CmdClick(button=token)  # type: ignore[arg-type]
        raise ValueError(f"Linha {line_no}: botão inválido '{parts[1]}'")
    if len(parts) == 3:
        return CmdClick(button="left", x=int(parts[1]), y=int(parts[2]))
    if len(parts) == 4:
        btn = parts[1].lower()
        if btn not in _VALID_BUTTONS:
            raise ValueError(f"Linha {line_no}: botão inválido '{parts[1]}'")
        return CmdClick(button=btn, x=int(parts[2]), y=int(parts[3]))  # type: ignore[arg-type]
    raise ValueError(f"Linha {line_no}: sintaxe click inválida")


class ScriptRunner:
    """Executa comandos parseados em thread dedicada via SendInput."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._current_line: Optional[int] = None
        self._last_error: Optional[str] = None
        self._on_done: Optional[Callable[[], None]] = None
        self._on_tick: Optional[Callable[[], None]] = None
        self._source_line = 0

    def set_on_done(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_done = callback

    def set_on_tick(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_tick = callback

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def current_line(self) -> Optional[int]:
        with self._lock:
            return self._current_line

    def last_error(self) -> Optional[str]:
        with self._lock:
            return self._last_error

    def run(self, source: str) -> bool:
        with self._lock:
            if self._running:
                return False
            try:
                commands = parse_script(source)
            except (ValueError, TypeError) as exc:
                self._last_error = str(exc)
                return False
            if not commands:
                self._last_error = "Script vazio"
                return False
            self._last_error = None
            self._stop_event.clear()
            self._running = True
            self._current_line = None
            self._thread = threading.Thread(
                target=self._run,
                args=(commands,),
                name="ScriptRunner",
                daemon=True,
            )
            self._thread.start()
            return True

    def stop(self) -> bool:
        with self._lock:
            if not self._running and self._thread is None:
                return False
            self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        with self._lock:
            self._running = False
            self._thread = None
            self._current_line = None
        return True

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "line": self._current_line,
                "last_error": self._last_error,
            }

    def _run(self, commands: list[Command]) -> None:
        try:
            self._exec_list(commands)
        except Exception as exc:
            with self._lock:
                self._last_error = str(exc)
        finally:
            with self._lock:
                self._running = False
                self._thread = None
                self._current_line = None
            done = self._on_done
            if done is not None:
                done()
            self._tick()

    def _exec_list(self, commands: list[Command]) -> None:
        for cmd in commands:
            if self._stop_event.is_set():
                return
            self._exec_one(cmd)

    def _exec_one(self, cmd: Command) -> None:
        if isinstance(cmd, CmdLoop):
            for _ in range(cmd.count):
                if self._stop_event.is_set():
                    return
                self._exec_list(list(cmd.body))
            return
        if isinstance(cmd, CmdWait):
            self._wait_ms(cmd.ms)
            return
        if isinstance(cmd, CmdMove):
            sendinput.move_absolute(cmd.x, cmd.y)
            self._tick()
            return
        if isinstance(cmd, CmdClick):
            if cmd.x is not None and cmd.y is not None:
                sendinput.click_at(cmd.button, cmd.x, cmd.y)
            else:
                sendinput.click(cmd.button)
            self._tick()
            return
        if isinstance(cmd, CmdKey):
            sendinput.key_press_name(cmd.key)
            self._tick()
            return

    def _wait_ms(self, ms: int) -> None:
        deadline = time.perf_counter() + (ms / 1000.0)
        while not self._stop_event.is_set():
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 0.01))

    def _tick(self) -> None:
        cb = self._on_tick
        if cb is not None:
            cb()
