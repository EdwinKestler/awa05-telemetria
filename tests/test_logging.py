import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from awa05.core.logging import configure_logging


def _cleanup_logger(logger):
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


class LoggingTests(unittest.TestCase):
    def test_configure_logging_writes_rotating_file(self):
        with tempfile.TemporaryDirectory() as temporal:
            log_path = Path(temporal) / "awa05.log"
            with patch(
                "awa05.core.logging.logging_config",
                return_value={
                    "enabled": True,
                    "level": "INFO",
                    "path": log_path,
                    "max_bytes": 1024,
                    "backup_count": 1,
                },
            ):
                logger = configure_logging(name="awa05.test.logging", console=False)
                logger.info("hello from test")

            for handler in logger.handlers:
                handler.flush()

            self.assertIn("hello from test", log_path.read_text(encoding="utf-8"))
            self.assertEqual(len(logger.handlers), 1)
            _cleanup_logger(logger)

    def test_configure_logging_is_idempotent_for_managed_handlers(self):
        with tempfile.TemporaryDirectory() as temporal:
            log_path = Path(temporal) / "awa05.log"
            config = {
                "enabled": True,
                "level": "INFO",
                "path": log_path,
                "max_bytes": 1024,
                "backup_count": 1,
            }
            with patch("awa05.core.logging.logging_config", return_value=config):
                logger = configure_logging(name="awa05.test.idempotent", console=False)
                logger = configure_logging(name="awa05.test.idempotent", console=False)

            self.assertEqual(len(logger.handlers), 1)
            _cleanup_logger(logger)

    def test_configure_logging_can_be_disabled(self):
        with patch(
            "awa05.core.logging.logging_config",
            return_value={
                "enabled": False,
                "level": "INFO",
                "path": "logs/awa05.log",
                "max_bytes": 1024,
                "backup_count": 1,
            },
        ):
            logger = configure_logging(name="awa05.test.disabled")

        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0], logging.NullHandler)
        _cleanup_logger(logger)


if __name__ == "__main__":
    unittest.main()
