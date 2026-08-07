"""ClickEngine — loop de cliques em thread dedicada com perf_counter."""

from __future__ import annotations

import random
import threading
import time
from typing import Callable, Optional

from core import sendinput
from core.types import ClickConfig, RuntimeState
from sequence.runner import SequenceRunner
from window_filter.filter import WindowFilter


class ClickEngine:
    """
    Motor de autoclique.

    - Thread dedicada com time.perf_counter para intervalo estável.
    - Jitter: intervalo_ms ± jitter_ms por espera.
    - Burst: N cliques com intervalo entre eles → pausa burst_pause_ms → repete.
    - Antes de cada clique: WindowFilter.allows(); se False, pula o clique.
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
        self._last_error: Optional[str] = None
        self._hold_pressed = False
        self._on_tick: Optional[Callable[[], None]] = None
        self._window_filter = WindowFilter()
        self._sequence = SequenceRunner()

    def set_on_tick(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_tick = callback

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

    def set_last_error(self, message: Optional[str]) -> None:
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
            self._hold_pressed = False
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
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        with self._lock:
            self._release_hold_if_needed()
            self._running = False
            self._thread = None
            return True

    def toggle(self) -> bool:
        if self.is_running():
            self.stop()
            return False
        self.start()
        return True

    def _release_hold_if_needed(self) -> None:
        if not self._hold_pressed:
            return
        try:
            sendinput.button_up(self._config.button)
        except OSError as exc:
            self._last_error = str(exc)
        finally:
            self._hold_pressed = False

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

    def _wait_interruptible(self, seconds: float) -> bool:
        """Espera até `seconds`. Retorna True se stop foi pedido."""
        if seconds <= 0:
            return self._stop_event.is_set()
        deadline = time.perf_counter() + seconds
        while True:
            if self._stop_event.is_set():
                return True
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                return False
            if self._stop_event.wait(timeout=min(remaining, 0.01)):
                return True

    def _resolve_target(self, config: ClickConfig) -> tuple[bool, int, int, Optional[int]]:
        """
        Retorna (use_fixed, x, y, step_delay_ms).

        step_delay_ms só vem da sequência; None = usar interval_ms.
        """
        if config.has_sequence() and not self._is_hold(config):
            target = self._sequence.peek()
            if target is not None:
                return True, target.x, target.y, target.delay_ms
        if config.position_mode == "fixed":
            return True, config.fixed_x, config.fixed_y, None
        return False, 0, 0, None

    def _perform_action(
        self,
        config: ClickConfig,
        use_fixed: bool,
        x: int,
        y: int,
    ) -> int:
        """Executa a ação do tick. Retorna quantos cliques contabilizar."""
        button = config.button

        if self._is_hold(config):
            if not self._hold_pressed:
                if use_fixed:
                    sendinput.move_absolute(x, y)
                sendinput.button_down(button)
                self._hold_pressed = True
                return 1
            return 0

        if config.click_type == "double":
            if use_fixed:
                sendinput.double_click_at(button, x, y)
            else:
                sendinput.double_click(button)
            return 2

        if use_fixed:
            sendinput.click_at(button, x, y)
        else:
            sendinput.click(button)
        return 1

    def _maybe_click(self, config: ClickConfig) -> tuple[int, Optional[int]]:
        """
        Tenta um clique se o filtro permitir.

        Retorna (clicks_added, step_delay_ms).
        Clique pulado pelo filtro: (0, None) e não avança a sequência.
        """
        if not self._window_filter.allows():
            return 0, None

        use_fixed, x, y, step_delay = self._resolve_target(config)
        added = self._perform_action(config, use_fixed, x, y)
        if added and config.has_sequence() and not self._is_hold(config):
            self._sequence.advance()
        return added, step_delay

    def _apply_click_result(self, added: int, config: ClickConfig, loop_start: float) -> bool:
        """Atualiza contador/limites. Retorna True se deve encerrar o loop."""
        with self._lock:
            if added:
                self._click_count += added
            if self._limits_reached(config, loop_start):
                self._running = False
                return True
        callback = self._on_tick
        if callback is not None:
            callback()
        return False

    def _run_loop(self) -> None:
        with self._lock:
            delay_ms = self._config.clamped_start_delay_ms()

        if delay_ms > 0:
            if self._wait_interruptible(delay_ms / 1000.0):
                with self._lock:
                    self._running = False
                return

        loop_start = time.perf_counter()
        try:
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
                except OSError as exc:
                    with self._lock:
                        self._last_error = str(exc)
                        self._running = False
                    break
        finally:
            with self._lock:
                self._release_hold_if_needed()
                self._running = False

    def _run_hold_tick(self, config: ClickConfig, loop_start: float) -> bool:
        """Um ciclo de hold. Retorna True se o loop deve encerrar."""
        added, _ = self._maybe_click(config)
        if self._apply_click_result(added, config, loop_start):
            return True
        if self._hold_pressed:
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

        for i in range(burst_n):
            if self._stop_event.is_set():
                return True

            config = self._snapshot_config()
            with self._lock:
                if self._limits_reached(config, loop_start):
                    self._running = False
                    return True

            added, step_delay = self._maybe_click(config)
            if step_delay is not None:
                last_step_delay = step_delay

            if self._apply_click_result(added, config, loop_start):
                return True

            # Entre cliques do burst
            if burst_enabled and i < burst_n - 1:
                wait_base = last_step_delay if last_step_delay is not None else None
                if self._wait_interruptible(self._interval_with_jitter_s(config, wait_base)):
                    return True

        config = self._snapshot_config()

        if burst_enabled:
            # Após o burst: só a pausa configurada (sem reaplicar interval)
            pause_ms = 0
            if config.burst_pause_ms is not None:
                pause_ms = max(0, int(config.burst_pause_ms))
            return self._wait_interruptible(pause_ms / 1000.0)

        # Ciclo normal: intervalo ± jitter (ou delay do passo da sequência)
        wait_base = last_step_delay if last_step_delay is not None else None
        return self._wait_interruptible(self._interval_with_jitter_s(config, wait_base))
