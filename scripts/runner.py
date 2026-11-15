"""ScriptRunner — DSL mínima: clique, movimento, espera, teclas, texto e loops."""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

from core import sendinput
from core.errors import ClickrError, error_from_exception
from core.keys import parse_key_sequence
from core.sendinput import ButtonName

MAX_LINES = 500
MAX_LOOP_COUNT = 1000
MAX_LOOP_DEPTH = 2
MAX_TYPE_LEN = 2000

_VALID_BUTTONS = frozenset({"left", "right", "middle", "x1", "x2"})
_DRAG_STEPS = 12
_DRAG_DURATION_S = 0.18


@dataclass(frozen=True)
class CmdClick:
    button: ButtonName
    x: Optional[int] = None
    y: Optional[int] = None
    double: bool = False
    line: int = 0


@dataclass(frozen=True)
class CmdMove:
    x: int
    y: int
    line: int = 0


@dataclass(frozen=True)
class CmdWait:
    ms: int
    max_ms: Optional[int] = None
    line: int = 0


@dataclass(frozen=True)
class CmdKey:
    key: str
    vks: tuple[int, ...] = ()
    line: int = 0


@dataclass(frozen=True)
class CmdType:
    text: str
    line: int = 0


@dataclass(frozen=True)
class CmdScroll:
    amount: int
    line: int = 0


@dataclass(frozen=True)
class CmdDrag:
    x1: int
    y1: int
    x2: int
    y2: int
    button: ButtonName = "left"
    line: int = 0


@dataclass(frozen=True)
class CmdLoop:
    count: int
    body: tuple[Any, ...]
    line: int = 0


Command = Union[CmdClick, CmdMove, CmdWait, CmdKey, CmdType, CmdScroll, CmdDrag, CmdLoop]


def _err(code: str, message: str, **params: Any) -> ClickrError:
    return ClickrError(f"script.{code}", message, **params)


def _int(line_no: int, token: str) -> int:
    try:
        return int(token)
    except (TypeError, ValueError):
        raise _err(
            "badNumber", f"Linha {line_no}: número inválido '{token}'", line=line_no, value=token
        ) from None


def _button(line_no: int, token: str) -> ButtonName:
    btn = token.lower()
    if btn not in _VALID_BUTTONS:
        raise _err(
            "badButton", f"Linha {line_no}: botão inválido '{token}'", line=line_no, value=token
        )
    return btn  # type: ignore[return-value]


def parse_combo(text: str) -> tuple[int, ...]:
    """'CTRL+SHIFT+A' → códigos VK na ordem de pressionamento. ValueError se inválido."""
    return parse_key_sequence(text)


def parse_script(source: str) -> list[Command]:
    """
    Analisa a DSL linha a linha.

    Gramática (por linha):
      click  [button] [x y]
      dclick [button] [x y]
      move x y
      drag x1 y1 x2 y2 [button]
      scroll N                 (positivo = para cima)
      wait ms | wait min-max   (min-max = espera aleatória)
      key NAME | key CTRL+C
      type "texto"
      loop N ... end
      # comentário
    """
    if source is None:
        raise _err("empty", "Script vazio")
    raw_lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if len(raw_lines) > MAX_LINES:
        raise _err("tooLong", f"Script excede {MAX_LINES} linhas", max=MAX_LINES)

    lines: list[tuple[int, str]] = []
    for i, line in enumerate(raw_lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append((i, stripped))

    commands, idx = _parse_block(lines, 0, depth=0)
    if idx < len(lines):
        line_no, text = lines[idx]
        raise _err(
            "unknownCommand", f"Linha {line_no}: token inesperado '{text}'", line=line_no, op=text
        )
    return commands


def _usage(line_no: int, usage: str) -> ClickrError:
    return _err("usage", f"Linha {line_no}: use '{usage}'", line=line_no, usage=usage)


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
                raise _err(
                    "endWithoutLoop",
                    f"Linha {line_no}: 'end' sem loop correspondente",
                    line=line_no,
                )
            return commands, i + 1

        if op == "loop":
            if depth >= MAX_LOOP_DEPTH:
                raise _err(
                    "loopDepth",
                    f"Linha {line_no}: profundidade de loop > {MAX_LOOP_DEPTH}",
                    line=line_no,
                    max=MAX_LOOP_DEPTH,
                )
            if len(parts) != 2:
                raise _usage(line_no, "loop N")
            count = _int(line_no, parts[1])
            if count < 1 or count > MAX_LOOP_COUNT:
                raise _err(
                    "loopRange",
                    f"Linha {line_no}: loop deve ser entre 1 e {MAX_LOOP_COUNT}",
                    line=line_no,
                    max=MAX_LOOP_COUNT,
                )
            body, next_i = _parse_block(lines, i + 1, depth + 1)
            commands.append(CmdLoop(count=count, body=tuple(body), line=line_no))
            i = next_i
            continue

        commands.append(_parse_simple(line_no, op, parts, text))
        i += 1

    if depth > 0:
        raise _err("loopNoEnd", "loop sem 'end'")
    return commands, i


def _parse_simple(line_no: int, op: str, parts: list[str], text: str) -> Command:
    if op in ("click", "dclick"):
        return _parse_click(line_no, parts, double=(op == "dclick"))
    if op == "move":
        if len(parts) != 3:
            raise _usage(line_no, "move X Y")
        return CmdMove(x=_int(line_no, parts[1]), y=_int(line_no, parts[2]), line=line_no)
    if op == "wait":
        if len(parts) != 2:
            raise _usage(line_no, "wait MS | wait MIN-MAX")
        return _parse_wait(line_no, parts[1])
    if op == "key":
        if len(parts) != 2:
            raise _usage(line_no, "key NOME | key CTRL+C")
        key = parts[1].upper()
        try:
            vks = parse_combo(key)
        except ValueError:
            raise _err(
                "badKey", f"Linha {line_no}: tecla não suportada '{parts[1]}'",
                line=line_no, value=parts[1],
            ) from None
        return CmdKey(key=key, vks=vks, line=line_no)
    if op == "type":
        rest = text[len(parts[0]):].strip()
        if not rest:
            raise _usage(line_no, 'type "texto"')
        return CmdType(text=_unquote(rest)[:MAX_TYPE_LEN], line=line_no)
    if op == "scroll":
        if len(parts) != 2:
            raise _usage(line_no, "scroll N")
        return CmdScroll(amount=_int(line_no, parts[1]), line=line_no)
    if op == "drag":
        if len(parts) not in (5, 6):
            raise _usage(line_no, "drag X1 Y1 X2 Y2 [botão]")
        nums = [_int(line_no, tok) for tok in parts[1:5]]
        btn: ButtonName = _button(line_no, parts[5]) if len(parts) == 6 else "left"
        return CmdDrag(*nums, button=btn, line=line_no)
    raise _err(
        "unknownCommand", f"Linha {line_no}: comando desconhecido '{op}'", line=line_no, op=op
    )


def _parse_wait(line_no: int, token: str) -> CmdWait:
    if "-" in token[1:]:
        low_s, _, high_s = token.partition("-") if not token.startswith("-") else ("", "", "")
        if not low_s or not high_s:
            raise _err("negativeWait", f"Linha {line_no}: wait não pode ser negativo", line=line_no)
        low, high = _int(line_no, low_s), _int(line_no, high_s)
        if high < low:
            low, high = high, low
        return CmdWait(ms=low, max_ms=high, line=line_no)
    ms = _int(line_no, token)
    if ms < 0:
        raise _err("negativeWait", f"Linha {line_no}: wait não pode ser negativo", line=line_no)
    return CmdWait(ms=ms, line=line_no)


def _unquote(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        text = text[1:-1]
    return (
        text.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\'", "'")
    )


def _parse_click(line_no: int, parts: list[str], double: bool) -> CmdClick:
    # click | click left | click 100 200 | click left 100 200
    n = len(parts)
    if n == 1:
        return CmdClick(button="left", double=double, line=line_no)
    if n == 2:
        return CmdClick(button=_button(line_no, parts[1]), double=double, line=line_no)
    if n == 3:
        return CmdClick(
            button="left", x=_int(line_no, parts[1]), y=_int(line_no, parts[2]),
            double=double, line=line_no,
        )
    if n == 4:
        return CmdClick(
            button=_button(line_no, parts[1]),
            x=_int(line_no, parts[2]),
            y=_int(line_no, parts[3]),
            double=double,
            line=line_no,
        )
    raise _usage(line_no, f"{parts[0].lower()} [botão] [X Y]")


class ScriptRunner:
    """Executa comandos parseados em thread dedicada via backend de input."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._current_line: Optional[int] = None
        self._last_error: Optional[dict[str, Any]] = None
        self._on_done: Optional[Callable[[], None]] = None
        self._on_tick: Optional[Callable[[], None]] = None
        self._held_button: Optional[str] = None
        self._held_keys: list[int] = []

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

    def last_error(self) -> Optional[dict[str, Any]]:
        with self._lock:
            return self._last_error

    def clear_error(self) -> None:
        with self._lock:
            self._last_error = None

    def run(self, source: str) -> bool:
        with self._lock:
            if self._running:
                return False
            try:
                commands = parse_script(source)
                if not commands:
                    raise _err("empty", "Script vazio")
            except (ValueError, TypeError) as exc:
                self._last_error = error_from_exception(exc)
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
        if (
            thread is not None
            and thread.is_alive()
            and thread is not threading.current_thread()
        ):
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
                line = self._current_line
                err = error_from_exception(exc)
                if line is not None:
                    err.setdefault("params", {})["line"] = line
                self._last_error = err
        finally:
            self._release_held()
            with self._lock:
                self._running = False
                self._thread = None
                self._current_line = None
            done = self._on_done
            if done is not None:
                try:
                    done()
                except Exception:
                    pass
            self._tick()

    def _release_held(self) -> None:
        button, self._held_button = self._held_button, None
        keys, self._held_keys = list(reversed(self._held_keys)), []
        try:
            if button is not None:
                sendinput.button_up(button)  # type: ignore[arg-type]
        except Exception:
            pass
        for vk in keys:
            try:
                sendinput.key_up(vk)
            except Exception:
                pass

    def _exec_list(self, commands: list[Command]) -> None:
        for cmd in commands:
            if self._stop_event.is_set():
                return
            self._exec_one(cmd)

    def _exec_one(self, cmd: Command) -> None:
        with self._lock:
            self._current_line = cmd.line or None
        if isinstance(cmd, CmdLoop):
            for _ in range(cmd.count):
                if self._stop_event.is_set():
                    return
                self._exec_list(list(cmd.body))
            return
        if isinstance(cmd, CmdWait):
            self._tick()
            ms = cmd.ms if cmd.max_ms is None else random.randint(cmd.ms, cmd.max_ms)
            self._wait_ms(ms)
            return
        if isinstance(cmd, CmdMove):
            sendinput.move_absolute(cmd.x, cmd.y)
        elif isinstance(cmd, CmdClick):
            self._click(cmd)
        elif isinstance(cmd, CmdKey):
            self._press_combo(cmd)
        elif isinstance(cmd, CmdType):
            sendinput.type_text(cmd.text)
        elif isinstance(cmd, CmdScroll):
            sendinput.scroll(cmd.amount)
        elif isinstance(cmd, CmdDrag):
            self._drag(cmd)
        self._tick()

    def _click(self, cmd: CmdClick) -> None:
        if cmd.x is not None and cmd.y is not None:
            if cmd.double:
                sendinput.double_click_at(cmd.button, cmd.x, cmd.y)
            else:
                sendinput.click_at(cmd.button, cmd.x, cmd.y)
        elif cmd.double:
            sendinput.double_click(cmd.button)
        else:
            sendinput.click(cmd.button)

    def _press_combo(self, cmd: CmdKey) -> None:
        vks = cmd.vks or parse_combo(cmd.key)
        for vk in vks:
            sendinput.key_down(vk)
            self._held_keys.append(vk)
        for vk in reversed(vks):
            sendinput.key_up(vk)
            self._held_keys.remove(vk)

    def _drag(self, cmd: CmdDrag) -> None:
        sendinput.move_absolute(cmd.x1, cmd.y1)
        sendinput.button_down(cmd.button)
        self._held_button = cmd.button
        self._wait_ms(30)
        for step in range(1, _DRAG_STEPS + 1):
            if self._stop_event.is_set():
                break
            frac = step / _DRAG_STEPS
            sendinput.move_absolute(
                round(cmd.x1 + (cmd.x2 - cmd.x1) * frac),
                round(cmd.y1 + (cmd.y2 - cmd.y1) * frac),
            )
            self._wait_ms(int(_DRAG_DURATION_S * 1000 / _DRAG_STEPS))
        sendinput.button_up(cmd.button)
        self._held_button = None

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
            try:
                cb()
            except Exception:
                pass
