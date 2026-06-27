import threading
import time

from awa05.config import scheduler_config
from awa05.core.orchestrator import TelemetryNode
from awa05.core.watchdog import watchdog_termico
from awa05.processing.dashboard import generar_dashboard_json
from awa05.telemetry.level import tomar_lectura
from awa05.upload.github import subir_archivos, subir_dashboard
from awa05.utils import ejecutar_seguro


def crear_nodo_telemetria():
    return TelemetryNode(
        read_level=tomar_lectura,
        generate_dashboard=generar_dashboard_json,
        upload_data=subir_archivos,
        upload_dashboard=subir_dashboard,
        watchdog=watchdog_termico,
    )


def job_lectura(node=None):
    node = node or crear_nodo_telemetria()
    print("[SCHEDULER] Tomando lectura del sensor...")
    resultado = node.run_telemetry_cycle()
    if resultado:
        print("[SCHEDULER] Datos generados y subidos.")
    else:
        print(
            "[SCHEDULER] Ciclo de lectura sin publicación. "
            f"Estado={node.current_state.value}"
        )
    return resultado


def job_sistema(node=None):
    node = node or crear_nodo_telemetria()
    print("[SCHEDULER] Actualizando KPIs del sistema Pi...")
    resultado = node.run_system_cycle()
    if not resultado:
        print(
            "[SCHEDULER] Ciclo de sistema falló. "
            f"Estado={node.current_state.value}"
        )
    return resultado


def job_watchdog(node=None):
    node = node or crear_nodo_telemetria()
    resultado = node.run_watchdog_cycle()
    if not resultado:
        print(f"[SCHEDULER] Watchdog falló. Estado={node.current_state.value}")
    return resultado


def iniciar_scheduler(schedule_module=None, node=None, run_forever=True):
    schedule = schedule_module
    if schedule is None:
        import schedule as schedule

    node = node or crear_nodo_telemetria()
    config = scheduler_config()
    espera_red = config["espera_red_minutos"]
    lectura_intervalo = config["lectura_intervalo_minutos"]
    kpi_intervalo = config["kpi_intervalo_minutos"]
    watchdog_intervalo = config["watchdog_intervalo_minutos"]

    print(f"[SCHEDULER] Esperando {espera_red} min para que la red levante...")
    node.start()
    time.sleep(espera_red * 60)
    node.network_ready()
    print("[SCHEDULER] Lectura inicial al arrancar...")
    ejecutar_seguro("lectura inicial", lambda: job_lectura(node))
    schedule.every(lectura_intervalo).minutes.do(
        ejecutar_seguro,
        "lectura",
        lambda: job_lectura(node),
    )
    schedule.every(kpi_intervalo).minutes.do(
        ejecutar_seguro,
        "KPIs del sistema",
        lambda: job_sistema(node),
    )
    schedule.every(watchdog_intervalo).minutes.do(
        ejecutar_seguro,
        "watchdog térmico",
        lambda: job_watchdog(node),
    )
    print(
        "[SCHEDULER] Activo - "
        f"lecturas cada {lectura_intervalo} min, "
        f"KPIs Pi cada {kpi_intervalo} min, "
        f"watchdog cada {watchdog_intervalo} min"
    )
    if not run_forever:
        return node
    while True:
        schedule.run_pending()
        time.sleep(60)


def iniciar_nodo():
    from awa05.drivers.ws2000 import iniciar_servidor

    hilo_flask = threading.Thread(target=iniciar_servidor, daemon=True)
    hilo_flask.start()
    print("[SERVIDOR] Flask iniciado en puerto 7777")
    iniciar_scheduler()


if __name__ == "__main__":
    iniciar_nodo()
