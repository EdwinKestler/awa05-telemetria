# awa05-telemetria
Sistema de monitoreo y telemetría ambiental - Cosechadora de agua AWA05

## Componentes

- `awa05/`: paquete Python introducido en la Fase 1 para alojar lógica
  importable y testeable.
- `scripts/read_ws2000.py`: recibe datos de la estación WS-2000 por HTTP en el puerto 7777.
- `scripts/read_distance.py`: mide el nivel con un sensor JSN-SR04T.
- `scripts/process_data.py`: genera `data/processed/dashboard_data.json`.
- `scripts/upload_github.py`: publica datos en una rama de datos por defecto.
- `scripts/scheduler.py`: coordina lecturas y publicación cada 15 minutos.

## Puesta en marcha en Raspberry Pi

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Crear `.env` en la raíz del repositorio:

```text
GITHUB_TOKEN=token_con_acceso_al_repositorio
AWA05_DATA_BRANCH=data
AWA05_DASHBOARD_BRANCH=data
AWA05_DRY_RUN=false
AWA05_ALLOW_MAIN_DATA=false
AWA05_ENABLE_SHUTDOWN=false
```

El archivo `.env` se carga con `python-dotenv` cuando está disponible. En la
Raspberry Pi, instale el paquete con `python -m pip install -e .` antes de
iniciar el servicio.

### Dispositivo Raspberry Pi de pruebas

La Raspberry Pi local `sakitron@192.168.1.40` se usa como dispositivo dummy de
pruebas de código/carga. No tiene conectados los sensores AWA05. Sus resultados
validan:

- instalación del paquete en Raspberry Pi OS;
- imports, pruebas y compatibilidad Python;
- arranque del scheduler y servidor Flask;
- modo dry-run de publicación;
- fallo seguro cuando no hay sensores.

No debe interpretarse como validación de hardware real de AWA05. Las lecturas
de JSN-SR04T/WS2000/peso deben validarse después en el hardware real o en una
banca con sensores conectados.

Por seguridad operacional, la publicación automática de datos queda dirigida a
`AWA05_DATA_BRANCH` y `AWA05_DASHBOARD_BRANCH` (`data` por defecto). Los commits
automáticos a `main` están bloqueados salvo que se active explícitamente
`AWA05_ALLOW_MAIN_DATA=true` después de aprobación humana.

Los dashboards HTML leen primero desde la rama `data` publicada en GitHub:

```text
https://raw.githubusercontent.com/geograficaaala/awa05-telemetria/data/data/processed/dashboard_data.json
```

Si esa URL no responde, usan como respaldo la ruta local
`./data/processed/dashboard_data.json`.

Para validar publicación sin escribir en GitHub:

```bash
AWA05_DRY_RUN=true python3 scripts/upload_github.py
```

Iniciar el servicio desde cualquier directorio:

```bash
python3 /ruta/a/awa05-telemetria/scripts/scheduler.py
```

Los scripts históricos permanecen como puntos de entrada compatibles. La nueva
lógica compartida debe ir migrando gradualmente al paquete `awa05/`.

En Fase 2, el receptor WS-2000 ya está encapsulado en
`awa05.drivers.ws2000.WS2000Receiver`. El script histórico
`scripts/read_ws2000.py` queda como shim de compatibilidad.

El sensor de peso no forma parte del pipeline activo de telemetría. En Fase 2
queda explícito como simulador (`awa05.drivers.weight.SimulatedWeightSensor`) y
como hardware no disponible hasta definir requisitos HX711 reales.

También existen entry points de paquete para validación gradual:

```bash
python3 -m awa05.upload.github
python3 -m awa05.telemetry.level
python3 -m awa05.core.scheduler
```

El scheduler espera 10 minutos para permitir que la red se conecte, inicia el
receptor WS-2000 y luego publica lecturas y KPIs cada 15 minutos.

Los intervalos operativos se leen desde `config/settings.json`:

- `scheduler.espera_red_minutos`
- `scheduler.lectura_intervalo_minutos`
- `scheduler.kpi_intervalo_minutos`
- `scheduler.watchdog_intervalo_minutos`

Para pruebas/smoke tests controlados pueden sobreescribirse temporalmente con:

- `AWA05_SCHEDULER_ESPERA_RED_MINUTOS`
- `AWA05_SCHEDULER_LECTURA_INTERVALO_MINUTOS`
- `AWA05_SCHEDULER_KPI_INTERVALO_MINUTOS`
- `AWA05_SCHEDULER_WATCHDOG_INTERVALO_MINUTOS`

La geometría y parámetros del JSN-SR04T también se leen desde
`config/settings.json`:

- `sensor_distancia.trig_gpio`
- `sensor_distancia.echo_gpio`
- `sensor_distancia.altura_total_cm`
- `sensor_distancia.altura_max_agua_cm`
- `sensor_distancia.radio_cm`
- `sensor_distancia.num_muestras`
- `sensor_distancia.pausa_muestras_s`
- `sensor_distancia.timeout_echo_s`

El receptor WS-2000 acepta el comportamiento histórico por defecto. Para
proteger `/data` con un secreto compartido:

```bash
export AWA05_WS2000_SHARED_SECRET='change-me'
```

Luego enviar el token con `X-AWA05-Token`, `token` como query parameter o
`token` como campo de formulario. El límite de payload se configura con
`ws2000.max_content_length_bytes` y puede sobreescribirse con
`AWA05_WS2000_MAX_CONTENT_LENGTH_BYTES`.

El watchdog térmico registra temperatura y genera un reporte cuando supera el
umbral configurado. El apagado automático de la Raspberry Pi está deshabilitado
por defecto; para habilitarlo se requiere `AWA05_ENABLE_SHUTDOWN=true` y debe
haber aprobación humana previa. Esto no controla ni corta la alimentación de la
máquina AWA05.

Los logs de runtime se configuran desde `config/settings.json`:

- `logging.enabled`
- `logging.level`
- `logging.path`
- `logging.max_bytes`
- `logging.backup_count`

También pueden sobreescribirse con:

- `AWA05_LOG_ENABLED`
- `AWA05_LOG_LEVEL`
- `AWA05_LOG_PATH`
- `AWA05_LOG_MAX_BYTES`
- `AWA05_LOG_BACKUP_COUNT`

Las publicaciones a GitHub tienen reintentos acotados para fallas transitorias
en operaciones reales de rama/archivo. No afectan `AWA05_DRY_RUN=true`.

- `AWA05_UPLOAD_RETRIES` (default: `2`)
- `AWA05_UPLOAD_RETRY_DELAY_S` (default: `5.0`)

## Verificación local

Las pruebas no requieren GPIO:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q awa05 scripts tests
```
