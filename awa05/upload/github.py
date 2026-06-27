import os
import time
from dataclasses import dataclass

from awa05.utils import cargar_entorno, ruta_proyecto, timestamp_ahora


REPO_NAME = "geograficaaala/awa05-telemetria"
RAMA = "main"

VALORES_TRUE = {"1", "true", "yes", "y", "si", "sí", "on"}


@dataclass
class ConfigPublicacion:
    repo_name: str = REPO_NAME
    app_branch: str = RAMA
    data_branch: str = "data"
    dashboard_branch: str = "data"
    dry_run: bool = False
    allow_main_data: bool = False
    create_data_branch: bool = True
    upload_retries: int = 2
    upload_retry_delay_s: float = 5.0


def _bool_env(nombre, default=False):
    valor = os.getenv(nombre)
    if valor is None:
        return default
    return valor.strip().lower() in VALORES_TRUE


def _int_env(nombre, default):
    valor = os.getenv(nombre)
    if valor in (None, ""):
        return default
    try:
        return int(valor)
    except ValueError:
        print(f"[CONFIG] Valor inválido para {nombre}: {valor!r}; usando {default}")
        return default


def _float_env(nombre, default):
    valor = os.getenv(nombre)
    if valor in (None, ""):
        return default
    try:
        return float(valor)
    except ValueError:
        print(f"[CONFIG] Valor inválido para {nombre}: {valor!r}; usando {default}")
        return default


def config_desde_env():
    cargar_entorno()
    data_branch = os.getenv("AWA05_DATA_BRANCH", "data").strip() or "data"
    return ConfigPublicacion(
        repo_name=os.getenv("AWA05_GITHUB_REPO", REPO_NAME).strip() or REPO_NAME,
        app_branch=os.getenv("AWA05_APP_BRANCH", RAMA).strip() or RAMA,
        data_branch=data_branch,
        dashboard_branch=os.getenv("AWA05_DASHBOARD_BRANCH", data_branch).strip() or data_branch,
        dry_run=_bool_env("AWA05_DRY_RUN", False),
        allow_main_data=_bool_env("AWA05_ALLOW_MAIN_DATA", False),
        create_data_branch=_bool_env("AWA05_CREATE_DATA_BRANCH", True),
        upload_retries=max(0, _int_env("AWA05_UPLOAD_RETRIES", 2)),
        upload_retry_delay_s=max(0.0, _float_env("AWA05_UPLOAD_RETRY_DELAY_S", 5.0)),
    )


def _leer_env_archivo():
    env_path = ruta_proyecto(".env")
    if not env_path.exists():
        return {}
    variables = {}
    with open(env_path, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            variables[clave.strip()] = valor.strip().strip('"').strip("'")
    return variables


def cargar_token():
    cargar_entorno()
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token
    token = _leer_env_archivo().get("GITHUB_TOKEN")
    if token:
        return token
    raise ValueError("Token no encontrado en .env")


ARCHIVOS = [
    "data/raw/nivel_raw.csv",
    "data/raw/clima_raw.csv",
]


def _github_repo(token, repo_name):
    from github import Auth, Github

    g = Github(auth=Auth.Token(token))
    return g.get_repo(repo_name)


def _unknown_object_exception():
    from github.GithubException import UnknownObjectException

    return UnknownObjectException


def _es_no_encontrado(error):
    return isinstance(error, _unknown_object_exception()) or getattr(error, "status", None) == 404


def _validar_branch_publicacion(branch, config, tipo):
    if branch == config.app_branch and not config.allow_main_data:
        print(
            f"[SKIP] {tipo}: publicación automática a {config.app_branch!r} "
            "bloqueada. Use AWA05_ALLOW_MAIN_DATA=true solo con aprobación humana."
        )
        return False
    return True


def _ejecutar_con_reintentos(nombre, operacion, retries, delay_s, sleep_fn=time.sleep):
    intento = 0
    while True:
        try:
            return operacion()
        except Exception as exc:
            if intento >= retries:
                print(
                    f"[ERROR] {nombre}: falló después de {intento + 1} intento(s): {exc}"
                )
                raise
            intento += 1
            print(
                f"[WARN] {nombre}: intento {intento} falló: {exc}. "
                f"Reintentando en {delay_s}s..."
            )
            if delay_s > 0:
                sleep_fn(delay_s)


def _asegurar_branch(repo, branch, source_branch, crear=True):
    if branch == source_branch:
        return
    try:
        repo.get_branch(branch)
    except Exception as e:
        if not _es_no_encontrado(e):
            raise
        if not crear:
            raise
        source = repo.get_branch(source_branch)
        repo.create_git_ref(ref=f"refs/heads/{branch}", sha=source.commit.sha)
        print(f"[OK] Rama de datos creada: {branch} desde {source_branch}")


def _publicar_archivo(repo, ruta_github, contenido, branch, mensaje):
    try:
        archivo = repo.get_contents(ruta_github, ref=branch)
        repo.update_file(
            path=ruta_github,
            message=mensaje,
            content=contenido,
            sha=archivo.sha,
            branch=branch,
        )
        print(f"[OK] Actualizado en {branch}: {ruta_github}")
    except Exception as e:
        if not _es_no_encontrado(e):
            raise
        repo.create_file(
            path=ruta_github,
            message=mensaje,
            content=contenido,
            branch=branch,
        )
        print(f"[OK] Creado en {branch}: {ruta_github}")


def subir_archivos(config=None):
    config = config or config_desde_env()
    branch = config.data_branch
    if not _validar_branch_publicacion(branch, config, "datos raw"):
        return

    if config.dry_run:
        print(f"[DRY-RUN] Datos raw se publicarían en {config.repo_name}@{branch}")
        repo = None
    else:
        token = cargar_token()
        repo = _github_repo(token, config.repo_name)
        _ejecutar_con_reintentos(
            f"asegurar rama {branch}",
            lambda: _asegurar_branch(
                repo,
                branch,
                config.app_branch,
                config.create_data_branch,
            ),
            config.upload_retries,
            config.upload_retry_delay_s,
        )

    for ruta_local in ARCHIVOS:
        ruta_absoluta = ruta_proyecto(ruta_local)
        if not ruta_absoluta.exists():
            print(f"[SKIP] No existe: {ruta_local}")
            continue
        with open(ruta_absoluta, "r", encoding="utf-8") as f:
            contenido = f.read()
        ruta_github = ruta_local
        mensaje = f"[datos] Actualizacion automatica {timestamp_ahora()}"
        if config.dry_run:
            print(f"[DRY-RUN] {ruta_github}: {len(contenido)} bytes -> {branch}")
            continue
        _ejecutar_con_reintentos(
            f"publicar {ruta_github}",
            lambda: _publicar_archivo(repo, ruta_github, contenido, branch, mensaje),
            config.upload_retries,
            config.upload_retry_delay_s,
        )


def subir_dashboard(config=None):
    config = config or config_desde_env()
    branch = config.dashboard_branch
    if not _validar_branch_publicacion(branch, config, "dashboard"):
        return

    ruta_local = "data/processed/dashboard_data.json"
    ruta_absoluta = ruta_proyecto(ruta_local)
    if not ruta_absoluta.exists():
        print("[SKIP] No existe dashboard_data.json")
        return
    with open(ruta_absoluta, "r", encoding="utf-8") as f:
        contenido = f.read()
    if config.dry_run:
        print(
            f"[DRY-RUN] {ruta_local}: {len(contenido)} bytes -> "
            f"{config.repo_name}@{branch}"
        )
        return

    token = cargar_token()
    repo = _github_repo(token, config.repo_name)
    _ejecutar_con_reintentos(
        f"asegurar rama {branch}",
        lambda: _asegurar_branch(repo, branch, config.app_branch, config.create_data_branch),
        config.upload_retries,
        config.upload_retry_delay_s,
    )
    _ejecutar_con_reintentos(
        f"publicar {ruta_local}",
        lambda: _publicar_archivo(
            repo,
            ruta_local,
            contenido,
            branch,
            f"[sistema] KPIs Pi {timestamp_ahora()}",
        ),
        config.upload_retries,
        config.upload_retry_delay_s,
    )


if __name__ == "__main__":
    subir_archivos()
