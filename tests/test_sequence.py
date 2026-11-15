from core.types import SequenceStep
from sequence.runner import SequenceRunner


def test_cycles_through_steps():
    r = SequenceRunner()
    r.reset([SequenceStep(1, 1, 10), SequenceStep(2, 2, 20)])
    assert r.peek().x == 1
    r.advance()
    assert r.peek().delay_ms == 20
    r.advance()
    assert r.peek().index == 0


def test_empty():
    r = SequenceRunner()
    assert r.peek() is None
    r.advance()
    assert not r.is_active()
