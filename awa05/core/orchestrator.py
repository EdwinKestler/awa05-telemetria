from awa05.core.context import StateTransition, TelemetryContext
from awa05.core.states import TelemetryState
from awa05.utils import timestamp_ahora


def _noop(*args, **kwargs):
    return None


class TelemetryNode:
    """Explicit state-machine shell for the AWA05 telemetry node.

    This first Phase 3 slice is intentionally injectable and side-effect-light:
    existing scheduler behavior is not replaced yet.  The scheduler can migrate
    to this class once the states and transition semantics are reviewed.
    """

    def __init__(
        self,
        read_level,
        generate_dashboard=_noop,
        upload_data=_noop,
        upload_dashboard=_noop,
        watchdog=_noop,
        max_sensor_failures=3,
        context=None,
        timestamp_fn=timestamp_ahora,
    ):
        self.read_level = read_level
        self.generate_dashboard = generate_dashboard
        self.upload_data = upload_data
        self.upload_dashboard = upload_dashboard
        self.watchdog = watchdog
        self.max_sensor_failures = max_sensor_failures
        self.context = context or TelemetryContext()
        self.timestamp_fn = timestamp_fn
        self.current_state = TelemetryState.BOOTING

    def transition_to(self, new_state, reason):
        new_state = TelemetryState(new_state)
        if new_state == self.current_state:
            return self.current_state
        print(
            "[STATE] "
            f"{self.current_state.value} -> {new_state.value}: {reason}"
        )
        self.context.transitions.append(
            StateTransition(
                from_state=self.current_state,
                to_state=new_state,
                reason=reason,
            )
        )
        self.current_state = new_state
        return self.current_state

    def start(self):
        return self.transition_to(TelemetryState.WAITING_NETWORK, "boot complete")

    def network_ready(self):
        return self.transition_to(TelemetryState.NORMAL, "network ready")

    def record_sensor_result(self, distance_cm, volume_l):
        if distance_cm is None:
            self.context.consecutive_sensor_failures += 1
            if self.context.consecutive_sensor_failures >= self.max_sensor_failures:
                self.transition_to(
                    TelemetryState.DEGRADED_SENSOR,
                    "sensor failure threshold reached",
                )
            return False

        self.context.last_distance_cm = distance_cm
        self.context.last_volume_l = volume_l
        self.context.last_successful_read_at = self.timestamp_fn()
        self.context.consecutive_sensor_failures = 0
        if self.current_state == TelemetryState.DEGRADED_SENSOR:
            self.transition_to(TelemetryState.NORMAL, "sensor recovered")
        return True

    def run_telemetry_cycle(self):
        if self.current_state == TelemetryState.BOOTING:
            self.start()
        if self.current_state == TelemetryState.WAITING_NETWORK:
            self.network_ready()

        try:
            distance_cm, volume_l = self.read_level()
            has_reading = self.record_sensor_result(distance_cm, volume_l)
            if not has_reading:
                return False

            previous_state = self.current_state
            self.generate_dashboard()
            self.transition_to(TelemetryState.UPLOADING, "publishing telemetry")
            self.upload_data()
            self.transition_to(previous_state, "telemetry published")
            return True
        except Exception as exc:
            self.context.last_error = str(exc)
            self.transition_to(TelemetryState.ERROR, "telemetry cycle failed")
            return False

    def run_system_cycle(self):
        try:
            previous_state = self.current_state
            self.generate_dashboard()
            self.transition_to(TelemetryState.UPLOADING, "publishing system dashboard")
            self.upload_dashboard()
            self.transition_to(previous_state, "system dashboard published")
            return True
        except Exception as exc:
            self.context.last_error = str(exc)
            self.transition_to(TelemetryState.ERROR, "system cycle failed")
            return False

    def run_watchdog_cycle(self):
        try:
            self.watchdog()
            return True
        except Exception as exc:
            self.context.last_error = str(exc)
            self.transition_to(TelemetryState.ERROR, "watchdog failed")
            return False
