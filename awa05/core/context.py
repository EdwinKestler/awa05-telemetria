from dataclasses import dataclass, field
from typing import List, Optional

from awa05.core.states import TelemetryState


@dataclass
class StateTransition:
    from_state: TelemetryState
    to_state: TelemetryState
    reason: str


@dataclass
class TelemetryContext:
    last_distance_cm: Optional[float] = None
    last_volume_l: Optional[float] = None
    consecutive_sensor_failures: int = 0
    last_error: Optional[str] = None
    transitions: List[StateTransition] = field(default_factory=list)
