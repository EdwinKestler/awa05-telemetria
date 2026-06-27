import json
from pathlib import Path

from awa05.utils import ruta_proyecto, timestamp_ahora


DEFAULT_HEALTH_PATH = "data/processed/health_status.json"


def _transition_to_dict(transition):
    return {
        "from_state": transition.from_state.value,
        "to_state": transition.to_state.value,
        "reason": transition.reason,
    }


def node_health(node, generated_at=None, max_transitions=20):
    context = node.context
    transitions = context.transitions[-max_transitions:]
    return {
        "generated_at": generated_at or timestamp_ahora(),
        "state": node.current_state.value,
        "last_distance_cm": context.last_distance_cm,
        "last_volume_l": context.last_volume_l,
        "last_successful_read_at": context.last_successful_read_at,
        "consecutive_sensor_failures": context.consecutive_sensor_failures,
        "last_error": context.last_error,
        "transition_count": len(context.transitions),
        "recent_transitions": [
            _transition_to_dict(transition) for transition in transitions
        ],
    }


def write_health_status(node, path=DEFAULT_HEALTH_PATH, generated_at=None):
    health_path = ruta_proyecto(path)
    health_path.parent.mkdir(parents=True, exist_ok=True)
    payload = node_health(node, generated_at=generated_at)
    temp_path = Path(f"{health_path}.tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(health_path)
    return health_path
