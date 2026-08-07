"""Tipos de configuração e estado runtime do motor de clique."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

ButtonName = Literal["left", "right", "middle", "x1", "x2"]
ClickType = Literal["single", "double", "hold"]
PositionMode = Literal["cursor", "fixed"]

_VALID_BUTTONS = frozenset({"left", "right", "middle", "x1", "x2"})
_VALID_CLICK_TYPES = frozenset({"single", "double", "hold"})
_VALID_POSITION_MODES = frozenset({"cursor", "fixed"})


@dataclass
class WindowFilterConfig:
    """Filtro de janela em foco (Tier 2)."""

    enabled: bool = False
    process: str = ""
    title_contains: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": bool(self.enabled),
            "process": str(self.process or ""),
            "title_contains": str(self.title_contains or ""),
        }

    @classmethod
    def from_dict(cls, data: Any) -> WindowFilterConfig:
        if not isinstance(data, dict):
            return cls()
        return cls(
            enabled=bool(data.get("enabled", False)),
            process=str(data.get("process") or ""),
            title_contains=str(data.get("title_contains") or ""),
        )


@dataclass
class SequenceStep:
    """Um passo da sequência multi-ponto (XY + delay após o clique)."""

    x: int = 0
    y: int = 0
    delay_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"x": int(self.x), "y": int(self.y), "delay_ms": max(0, int(self.delay_ms))}

    @classmethod
    def from_dict(cls, data: Any) -> SequenceStep:
        if not isinstance(data, dict):
            raise ValueError("Passo de sequência inválido")
        return cls(
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            delay_ms=max(0, int(data.get("delay_ms", 0) or 0)),
        )


@dataclass
class ClickConfig:
    """Contrato de configuração (núcleo + Tier 1 + Tier 2)."""

    interval_ms: int = 80
    jitter_ms: int = 0
    button: ButtonName = "left"
    click_type: ClickType = "single"
    position_mode: PositionMode = "cursor"
    fixed_x: int = 0
    fixed_y: int = 0
    hold: bool = False
    start_delay_ms: int = 0
    max_clicks: Optional[int] = None
    max_duration_ms: Optional[int] = None
    burst_count: Optional[int] = None
    burst_pause_ms: Optional[int] = None
    sequence: list[SequenceStep] = field(default_factory=list)
    window_filter: WindowFilterConfig = field(default_factory=WindowFilterConfig)
    hotkey: str = "F6"
    always_on_top: bool = True
    compact_mode: bool = False

    def clamped_interval_ms(self) -> int:
        return max(1, int(self.interval_ms))

    def clamped_jitter_ms(self) -> int:
        return max(0, int(self.jitter_ms))

    def clamped_start_delay_ms(self) -> int:
        return max(0, int(self.start_delay_ms))

    def has_sequence(self) -> bool:
        return len(self.sequence) > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "interval_ms": int(self.interval_ms),
            "jitter_ms": int(self.jitter_ms),
            "button": self.button,
            "click_type": self.click_type,
            "position_mode": self.position_mode,
            "fixed_x": int(self.fixed_x),
            "fixed_y": int(self.fixed_y),
            "hold": bool(self.hold),
            "start_delay_ms": int(self.start_delay_ms),
            "max_clicks": self.max_clicks,
            "max_duration_ms": self.max_duration_ms,
            "burst_count": self.burst_count,
            "burst_pause_ms": self.burst_pause_ms,
            "sequence": [s.to_dict() for s in self.sequence],
            "window_filter": self.window_filter.to_dict(),
            "hotkey": self.hotkey,
            "always_on_top": bool(self.always_on_top),
            "compact_mode": bool(self.compact_mode),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClickConfig:
        base = cls().to_dict()
        known = set(base.keys())
        merged = {k: v for k, v in data.items() if k in known}

        if "max_clicks" in merged:
            merged["max_clicks"] = cls._optional_positive_int(merged["max_clicks"])
        if "max_duration_ms" in merged:
            merged["max_duration_ms"] = cls._optional_positive_int(merged["max_duration_ms"])
        if "burst_count" in merged:
            merged["burst_count"] = cls._optional_positive_int(merged["burst_count"])
        if "burst_pause_ms" in merged:
            merged["burst_pause_ms"] = cls._optional_non_negative_int(merged["burst_pause_ms"])
        if "start_delay_ms" in merged and merged["start_delay_ms"] is not None:
            merged["start_delay_ms"] = max(0, int(merged["start_delay_ms"]))
        if "interval_ms" in merged and merged["interval_ms"] is not None:
            merged["interval_ms"] = max(1, int(merged["interval_ms"]))
        if "jitter_ms" in merged and merged["jitter_ms"] is not None:
            merged["jitter_ms"] = max(0, int(merged["jitter_ms"]))
        if "hotkey" in merged and merged["hotkey"] is not None:
            merged["hotkey"] = str(merged["hotkey"]).upper()
        if "always_on_top" in merged:
            merged["always_on_top"] = bool(merged["always_on_top"])
        if "compact_mode" in merged:
            merged["compact_mode"] = bool(merged["compact_mode"])
        if "hold" in merged:
            merged["hold"] = bool(merged["hold"])
        if "button" in merged and merged["button"] is not None:
            btn = str(merged["button"]).lower()
            if btn not in _VALID_BUTTONS:
                btn = "left"
            merged["button"] = btn
        if "click_type" in merged and merged["click_type"] is not None:
            ct = str(merged["click_type"]).lower()
            if ct not in _VALID_CLICK_TYPES:
                ct = "single"
            merged["click_type"] = ct
        if "position_mode" in merged and merged["position_mode"] is not None:
            pm = str(merged["position_mode"]).lower()
            if pm not in _VALID_POSITION_MODES:
                pm = "cursor"
            merged["position_mode"] = pm
        if "fixed_x" in merged and merged["fixed_x"] is not None:
            merged["fixed_x"] = int(merged["fixed_x"])
        if "fixed_y" in merged and merged["fixed_y"] is not None:
            merged["fixed_y"] = int(merged["fixed_y"])
        if "sequence" in merged:
            merged["sequence"] = cls._parse_sequence(merged["sequence"])
        if "window_filter" in merged:
            merged["window_filter"] = WindowFilterConfig.from_dict(merged["window_filter"])

        flat = {**base, **merged}
        seq = flat.pop("sequence")
        wf = flat.pop("window_filter")
        if isinstance(seq, list) and seq and isinstance(seq[0], SequenceStep):
            sequence = seq
        else:
            sequence = cls._parse_sequence(seq)
        if isinstance(wf, WindowFilterConfig):
            window_filter = wf
        else:
            window_filter = WindowFilterConfig.from_dict(wf)
        return cls(**flat, sequence=sequence, window_filter=window_filter)

    @staticmethod
    def _parse_sequence(value: Any) -> list[SequenceStep]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("sequence deve ser uma lista")
        steps: list[SequenceStep] = []
        for item in value:
            if isinstance(item, SequenceStep):
                steps.append(item)
            else:
                steps.append(SequenceStep.from_dict(item))
        return steps

    @staticmethod
    def _optional_positive_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        n = int(value)
        if n <= 0:
            return None
        return n

    @staticmethod
    def _optional_non_negative_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        n = int(value)
        if n < 0:
            return None
        return n


@dataclass
class RuntimeState:
    """Estado exposto à UI via bridge."""

    running: bool = False
    click_count: int = 0
    started_at: Optional[float] = None
    last_error: Optional[str] = None
    config: ClickConfig = field(default_factory=ClickConfig)
    picking: bool = False
    recording_hotkey: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "click_count": self.click_count,
            "started_at": self.started_at,
            "last_error": self.last_error,
            "config": self.config.to_dict(),
            "picking": self.picking,
            "recording_hotkey": self.recording_hotkey,
        }
