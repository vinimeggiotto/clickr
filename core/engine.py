"""ClickEngine — loop de cliques em thread dedicada com perf_counter."""

from __future__ import annotations

import random
import sys
import threading
import time
from typing import Callable, Optional

from core import sendinput
from core.keys import parse_key_sequence
from core.types import ClickConfig, RuntimeState
from sequence.runner import SequenceRunner
from window_filter.filter import WindowFilter

# Atraso acima do qual o agendamento é ressincronizado em vez de "correr atrás".
_RESYNC_LATE_S = 0.02
# Trecho final da espera feito em espera ativa para precisão de sub-milissegundo.
_SPIN_S = 0.0015


class _TimerResolution:
    """Eleva a resolução do timer do Windows para 1 ms enquanto o motor roda."""

    def __init__(self) -> None:
        self._winmm = None
        if sys.platform == "win32":
            try:
                import ctypes

                self._winmm = ctypes.WinDLL("winmm")
            except OSError:
                self._winmm = None

    def __enter__(self) -> "_TimerResolution":
        if self._winmm is not None:
            self._winmm.timeBeginPeriod(1)
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._winmm is not None:
            self._winmm.timeEndPeriod(1)


class ClickEngine:
    """
    Motor de autoclique.

    - Thread dedicada; cada espera mira um instante agendado (deadline), de modo
      que o tempo gasto na própria ação não se soma ao intervalo.
    - Jitter: intervalo_ms ± jitter_ms por espera.
    - Burst: N cliques com intervalo entre eles → pausa burst_pause_ms → repete.
    - Antes de cada clique: WindowFilter.allows() e o guard de clique (ex.: não
      clicar na própria janela do Clickr); se bloqueado, pula o clique.
    - Sequência multi-ponto via SequenceRunner quando sequence não está vazia.
    - Botões: left / right / middle / x1 / x2.
    """

    def __init__(self) -> None:
        self._config = ClickConfig()
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._click_count = 0
        self._started_at: Optional[float] = None
        self._last_error: Optional[object] = None
        self._hold_button: Optional[str] = None
        self._hold_keys: tuple = ()
        self._key_guard: Optional[Callable[[], bool]] = None
        self._on_tick: Optional[Callable[[], None]] = None
        self._click_guard: Optional[Callable[[int, int], bool]] = None
        self._window_filter = WindowFilter()
        self._sequence = SequenceRunner()
        self._due: Optional[float] = None

    def set_on_tick(self, callback: Optional[Callable[[], None]]) -> None:
        """Callback leve chamado a cada mudança de estado (deve só sinalizar)."""
        self._on_tick = callback

    def set_click_guard(self, guard: Optional[Callable[[int, int], bool]]) -> None:
        """guard(x, y) → True bloqueia o clique naquele ponto de tela."""
        self._click_guard = guard

    def set_key_guard(self, guard: Optional[Callable[[], bool]]) -> None:
        """guard() → True bloqueia o envio de teclas (ex.: Clickr em foco)."""
        self._key_guard = guard

    @property
    def window_filter(self) -> WindowFilter:
        return self._window_filter

    def get_config(self) -> ClickConfig:
        with self._lock:
            return ClickConfig.from_dict(self._config.to_dict())

    def update_config(self, data: dict) -> ClickConfig:
        with self._lock:
            current = self._config.to_dict()
            current.update({k: v for k, v in data.items() if k in current})
            self._config = ClickConfig.from_dict(current)
            self._window_filter.configure(self._config.window_filter)
            self._sequence.set_steps(self._config.sequence)
            return ClickConfig.from_dict(self._config.to_dict())

    def get_state(self) -> RuntimeState:
        with self._lock:
            return RuntimeState(
                running=self._running,
                click_count=self._click_count,
                started_at=self._started_at,
                last_error=self._last_error,
                config=ClickConfig.from_dict(self._config.to_dict()),
            )

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def set_last_error(self, message: Optional[object]) -> None:
        with self._lock:
            self._last_error = message

    def start(self) -> bool:
        with self._lock:
            if self._running:
                return False
            self._last_error = None
            self._click_count = 0
            self._started_at = time.time()
            self._stop_event.clear()
            self._running = True
            self._hold_button = None
            self._hold_keys = ()
            self._due = None
            self._window_filter.configure(self._config.window_filter)
            self._sequence.reset(self._config.sequence)
            self._thread = threading.Thread(
                target=self._run_loop,
                name="ClickEngine",
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
            self._release_hold_if_needed()
            self._running = False
            self._thread = None
        self._emit()
        return True

    def toggle(self) -> bool:
        if self.is_running():
            self.stop()
            return False
        self.start()
        return True

    # --- Interno -------------------------------------------------------

    def _emit(self) -> None:
        callback = self._on_tick
        if callback is None:
            return
        try:
            callback()
        except Exception:
            pass

    def _release_hold_if_needed(self) -> None:
        button, self._hold_button = self._hold_button, None
        keys, self._hold_keys = self._hold_keys, ()
        try:
            if button is not None:
                sendinput.button_up(button)  # type: ignore[arg-type]
            for vk in reversed(keys):
                sendinput.key_up(vk)
        except (OSError, ValueError) as exc:
            self._last_error = str(exc)

    @property
    def _holding(self) -> bool:
        return self._hold_button is not None or bool(self._hold_keys)

    def _is_hold(self, config: ClickConfig) -> bool:
        return config.click_type == "hold" or config.hold

    def _limits_reached(self, config: ClickConfig, loop_start: float) -> bool:
        if config.max_clicks is not None and self._click_count >= config.max_clicks:
            return True
        if config.max_duration_ms is not None:
            elapsed_ms = (time.perf_counter() - loop_start) * 1000.0
            if elapsed_ms >= config.max_duration_ms:
                return True
        return False

    def _snapshot_config(self) -> ClickConfig:
        with self._lock:
            return ClickConfig.from_dict(self._config.to_dict())

    def _interval_with_jitter_s(self, config: ClickConfig, base_ms: Optional[int] = None) -> float:
        base = config.clamped_interval_ms() if base_ms is None else max(0, int(base_ms))
        jitter = config.clamped_jitter_ms()
        if jitter <= 0:
            return max(0.0, base / 1000.0)
        delta = random.randint(-jitter, jitter)
        return max(0.0, (base + delta) / 1000.0)

    def _wait_until(self, deadline: float) -> bool:
        """Espera até o instante `deadline` (perf_counter). True se stop foi pedido."""
        while True:
            if self._stop_event.is_set():
                return True
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                return False
            if remaining > _SPIN_S:
                if self._stop_event.wait(timeout=min(remaining - _SPIN_S, 0.05)):
                    return True
            else:
                time.sleep(0)

    def _wait_interruptible(self, seconds: float) -> bool:
        """Espera `seconds` a partir de agora. True se stop foi pedido."""
        if seconds <= 0:
            return self._stop_event.is_set()
        return self._wait_until(time.perf_counter() + seconds)

    def _anchor(self) -> float:
        """Instante de referência do tick atual (agendado, ou agora se atrasado)."""
        now = time.perf_counter()
        due = self._due
        if due is None or (now - due) > _RESYNC_LATE_S:
            return now
        return due

    def _wait_from(self, anchor: float, seconds: float) -> bool:
        """Agenda o próximo tick para anchor + seconds e espera até lá."""
        self._due = anchor + max(0.0, seconds)
        return self._wait_until(self._due)

    def _resolve_target(self, config: ClickConfig) -> tuple[bool, int, int, Optional[int]]:
        """
        Retorna (use_fixed, x, y, step_delay_ms).

        step_delay_ms só vem da sequência; None = usar interval_ms.
        O jitter de posição desloca pontos fixos/da sequência; no modo cursor
        não se aplica (o cursor é do usuário).
        """
        jitter = max(0, int(config.position_jitter_px))
        dx = random.randint(-jitter, jitter) if jitter else 0
        dy = random.randint(-jitter, jitter) if jitter else 0
        if config.has_sequence() and not self._is_hold(config):
            target = self._sequence.peek()
            if target is not None:
                return True, target.x + dx, target.y + dy, target.delay_ms
        if config.position_mode == "fixed":
            return True, config.fixed_x + dx, config.fixed_y + dy, None
        return False, 0, 0, None

    def _guard_blocks(self, use_fixed: bool, x: int, y: int) -> bool:
        guard = self._click_guard
        if guard is None:
            return False
        try:
            if not use_fixed:
                x, y = sendinput.get_cursor_pos()
            return bool(guard(int(x), int(y)))
        except Exception:
            return False

    def _key_guard_blocks(self) -> bool:
        guard = self._key_guard
        if guard is None:
            return False
        try:
            return bool(guard())
        except Exception:
            return False

    def _perform_key_action(self, config: ClickConfig) -> int:
        """Ação de teclado: pressiona a tecla/combinação configurada."""
        vks = parse_key_sequence(config.key_name)
        if self._is_hold(config):
            if self._hold_keys:
                return 0
            for vk in vks:
                sendinput.key_down(vk)
            self._hold_keys = tuple(vks)
            return 1
        times = 2 if config.click_type == "double" else 1
        for _ in range(times):
            for vk in vks:
                sendinput.key_down(vk)
            for vk in reversed(vks):
                sendinput.key_up(vk)
        return times

    def _perform_action(
        self,
        config: ClickConfig,
        use_fixed: bool,
        x: int,
        y: int,
    ) -> int:
        """Executa a ação do tick. Retorna quantos cliques contabilizar."""
        button = config.button
        restore = bool(config.restore_cursor)

        if self._is_hold(config):
            if self._hold_button is None:
                if use_fixed:
                    sendinput.move_absolute(x, y)
                sendinput.button_down(button)
                self._hold_button = button
                return 1
            return 0

        if config.click_type == "double":
            if use_fixed:
                sendinput.double_click_at(button, x, y, restore=restore)
            else:
                sendinput.double_click(button)
            return 2

        if use_fixed:
            sendinput.click_at(button, x, y, restore=restore)
        else:
            sendinput.click(button)
        return 1

    def _maybe_click(self, config: ClickConfig) -> tuple[int, Optional[int]]:
        """
        Tenta uma ação se o filtro e os guards permitirem.

        Retorna (clicks_added, step_delay_ms).
        Ação pulada: (0, None) e não avança a sequência.
        """
        if not self._window_filter.allows():
            return 0, None

        if config.action == "key":
            if self._key_guard_blocks():
                return 0, None
            return self._perform_key_action(config), None

        use_fixed, x, y, step_delay = self._resolve_target(config)
        if self._guard_blocks(use_fixed, x, y):
            return 0, None
        added = self._perform_action(config, use_fixed, x, y)
        if added and config.has_sequence() and not self._is_hold(config):
            self._sequence.advance()
        return added, step_delay

    def _apply_click_result(self, added: int, config: ClickConfig, loop_start: float) -> bool:
        """Atualiza contador/limites. Retorna True se deve encerrar o loop."""
        with self._lock:
            if added:
                self._click_count += added
            done = self._limits_reached(config, loop_start)
            if done:
                self._running = False
        self._emit()
        return done

    def _run_loop(self) -> None:
        try:
            with _TimerResolution():
                self._run_loop_inner()
        finally:
            with self._lock:
                self._release_hold_if_needed()
                self._running = False
            # Sempre avisa a UI no fim (limite atingido, erro ou stop).
            self._emit()

    def _run_loop_inner(self) -> None:
        with self._lock:
            delay_ms = self._config.clamped_start_delay_ms()

        if delay_ms > 0:
            self._emit()
            if self._wait_interruptible(delay_ms / 1000.0):
                return

        loop_start = time.perf_counter()
        self._due = None
        while not self._stop_event.is_set():
            config = self._snapshot_config()
            with self._lock:
                if self._limits_reached(config, loop_start):
                    self._running = False
                    break

            try:
                if self._is_hold(config):
                    if self._run_hold_tick(config, loop_start):
                        break
                    continue

                if self._run_click_cycle(config, loop_start):
                    break
            except (OSError, ValueError) as exc:
                with self._lock:
                    self._last_error = str(exc)
                    self._running = False
                break

    def _run_hold_tick(self, config: ClickConfig, loop_start: float) -> bool:
        """Um ciclo de hold. Retorna True se o loop deve encerrar."""
        added, _ = self._maybe_click(config)
        if self._apply_click_result(added, config, loop_start):
            return True
        if self._holding:
            return self._wait_interruptible(0.05)
        # Filtro bloqueou o press — espera intervalo e tenta de novo
        return self._wait_interruptible(self._interval_with_jitter_s(config))

    def _run_click_cycle(self, config: ClickConfig, loop_start: float) -> bool:
        """
        Um ciclo: 1 clique (ou burst_count cliques) + espera apropriada.

        Retorna True se o loop deve encerrar.
        """
        burst_enabled = config.burst_count is not None
        burst_n = config.burst_count if burst_enabled else 1
        last_step_delay: Optional[int] = None
        anchor = self._anchor()

        for i in range(burst_n):
            if self._stop_event.is_set():
                return True

            config = self._snapshot_config()
            with self._lock:
                if self._limits_reached(config, loop_start):
                    self._running = False
                    return True

            anchor = self._anchor()
            added, step_delay = self._maybe_click(config)
            if step_delay is not None:
                last_step_delay = step_delay

            if self._apply_click_result(added, config, loop_start):
                return True

            # Entre cliques do burst
            if burst_enabled and i < burst_n - 1:
                if self._wait_from(anchor, self._interval_with_jitter_s(config, last_step_delay)):
                    return True

        config = self._snapshot_config()

        if burst_enabled:
            # Após o burst: só a pausa configurada (sem reaplicar interval)
            pause_ms = 0
            if config.burst_pause_ms is not None:
                pause_ms = max(0, int(config.burst_pause_ms))
            return self._wait_from(anchor, pause_ms / 1000.0)

        # Ciclo normal: intervalo ± jitter (ou delay do passo da sequência)
        return self._wait_from(anchor, self._interval_with_jitter_s(config, last_step_delay))
