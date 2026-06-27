import logging
from logging.handlers import RotatingFileHandler

from awa05.config import logging_config
from awa05.utils import ruta_proyecto


MANAGED_HANDLER_ATTR = "_awa05_managed_handler"


def _level_from_name(level):
    if isinstance(level, int):
        return level
    return getattr(logging, str(level).upper(), logging.INFO)


def _remove_managed_handlers(logger):
    for handler in list(logger.handlers):
        if getattr(handler, MANAGED_HANDLER_ATTR, False):
            logger.removeHandler(handler)
            handler.close()


def configure_logging(
    name="awa05",
    enabled=None,
    level=None,
    path=None,
    max_bytes=None,
    backup_count=None,
    console=True,
):
    config = logging_config()
    if enabled is None:
        enabled = config["enabled"]
    if level is None:
        level = config["level"]
    if path is None:
        path = config["path"]
    if max_bytes is None:
        max_bytes = config["max_bytes"]
    if backup_count is None:
        backup_count = config["backup_count"]

    logger = logging.getLogger(name)
    logger.setLevel(_level_from_name(level))
    logger.propagate = False
    _remove_managed_handlers(logger)

    if not enabled:
        logger.addHandler(logging.NullHandler())
        setattr(logger.handlers[-1], MANAGED_HANDLER_ATTR, True)
        return logger

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    log_path = ruta_proyecto(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    setattr(file_handler, MANAGED_HANDLER_ATTR, True)
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        setattr(console_handler, MANAGED_HANDLER_ATTR, True)
        logger.addHandler(console_handler)

    return logger
