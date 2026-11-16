from core.types import ClickConfig, SequenceStep


def test_defaults_roundtrip():
    cfg = ClickConfig()
    assert ClickConfig.from_dict(cfg.to_dict()).to_dict() == cfg.to_dict()


def test_unknown_keys_are_ignored():
    cfg = ClickConfig.from_dict({"interval_ms": 50, "nao_existe": 1})
    assert cfg.interval_ms == 50


def test_clamps_and_optionals():
    cfg = ClickConfig.from_dict(
        {"interval_ms": 0, "jitter_ms": -5, "max_clicks": 0, "burst_pause_ms": -1, "button": "zzz"}
    )
    assert cfg.interval_ms == 1
    assert cfg.jitter_ms == 0
    assert cfg.max_clicks is None
    assert cfg.burst_pause_ms is None
    assert cfg.button == "left"


def test_sequence_parsing():
    cfg = ClickConfig.from_dict({"sequence": [{"x": 1, "y": 2, "delay_ms": 3}]})
    assert cfg.sequence == [SequenceStep(1, 2, 3)]
    assert cfg.has_sequence()
