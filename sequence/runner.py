"""SequenceRunner — avança lista de pontos XY com delay por passo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.types import SequenceStep


@dataclass(frozen=True)
class SequenceTarget:
    """Alvo do próximo clique na sequência."""

    x: int
    y: int
    delay_ms: int
    index: int


class SequenceRunner:
    """
    Mantém o índice do passo atual e devolve o próximo alvo.

    Após consumir um passo, o delay_ms do passo é a espera pós-clique
    sugerida para o motor (além do intervalo base, o engine usa este valor
    quando a sequência está ativa).
    """

    def __init__(self) -> None:
        self._steps: list[SequenceStep] = []
        self._index: int = 0

    def reset(self, steps: Optional[list[SequenceStep]] = None) -> None:
        if steps is not None:
            self._steps = [SequenceStep(x=s.x, y=s.y, delay_ms=s.delay_ms) for s in steps]
        self._index = 0

    def set_steps(self, steps: list[SequenceStep]) -> None:
        self._steps = [SequenceStep(x=s.x, y=s.y, delay_ms=s.delay_ms) for s in steps]
        if self._index >= len(self._steps):
            self._index = 0

    def is_active(self) -> bool:
        return len(self._steps) > 0

    def __len__(self) -> int:
        return len(self._steps)

    def peek(self) -> Optional[SequenceTarget]:
        if not self._steps:
            return None
        step = self._steps[self._index]
        return SequenceTarget(
            x=step.x,
            y=step.y,
            delay_ms=max(0, int(step.delay_ms)),
            index=self._index,
        )

    def advance(self) -> None:
        if not self._steps:
            return
        self._index = (self._index + 1) % len(self._steps)

    def current_index(self) -> int:
        return self._index
