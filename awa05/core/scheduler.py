import threading
import time

from awa05.config import scheduler_config
from awa05.core.watchdog import watchdog_termico
from awa05.processing.dashboard import generar_dashboard_json
from awa05.telemetry.level import tomar_lectura
from awa05.upload.github import subir_archivos, subir_dashboard
from awa05.utils import ejecutar_seguro


def job_lectura():
    print("[SCHEDULER] Tomando lectura del sensor...")
    tomar_lectura()
    print("[SCHEDULER] Generando y subiendo datos...")
    generar_dashboard_json()
    subir_archivos()


def job_sistema():
    print("[SCHEDULER] Actualizando KPIs del sistema Pi...")
    generar_dashboard_json()
    subir_dashboard()


def iniciar_scheduler(schedule_module=None):
    schedule = schedule_module
    if schedule is None:
        import schedule as schedule

    config = scheduler_config()
    espera_red = config["espera_red_minutos"]
    lectura_intervalo = config["lectura_intervalo_minutos"]
    kpi_intervalo = config["kpi_intervalo_minutos"]
    watchdog_intervalo = config["watchdog_intervalo_minutos"]

    print(f"[SCHEDULER] Esperando {espera_red} min para que la red levante...")
    time.sleep(espera_red * 60)
    print("[SCHEDULER] Lectura inicial al arrancar...")
    ejecutar_seguro("lectura inicial", job_lectura)
    schedule.every(lectura_intervalo).minutes.do(ejecutar_seguro, "lectura", job_lectura)
    schedule.every(kpi_intervalo).minutes.do(ejecutar_seguro, "KPIs del sistema", job_sistema)
    schedule.every(watchdog_intervalo).minutes.do(ejecutar_seguro, "watchdog térmico", watchdog_termico)
    print(
        "[SCHEDULER] Activo - "
        f"lecturas cada {lectura_intervalo} min, "
        f"KPIs Pi cada {kpi_intervalo} min, "
        f"watchdog cada {watchdog_intervalo} min"
    )
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
