import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from awa05.upload.github import ConfigPublicacion, subir_archivos, subir_dashboard


class UploadGithubTests(unittest.TestCase):
    def test_subir_archivos_dry_run_no_pide_token_ni_cliente(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = Path(temporal) / "nivel_raw.csv"
            archivo.write_text("timestamp,volumen_litros\n2026-01-01,1.0\n", encoding="utf-8")
            config = ConfigPublicacion(dry_run=True, data_branch="data")

            with patch("awa05.upload.github.ARCHIVOS", [archivo]), \
                 patch("awa05.upload.github.cargar_token") as cargar_token, \
                 patch("awa05.upload.github._github_repo") as github_repo:
                subir_archivos(config)

        cargar_token.assert_not_called()
        github_repo.assert_not_called()

    def test_bloquea_datos_a_main_sin_aprobacion(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = Path(temporal) / "nivel_raw.csv"
            archivo.write_text("timestamp,volumen_litros\n2026-01-01,1.0\n", encoding="utf-8")
            config = ConfigPublicacion(data_branch="main", allow_main_data=False)

            with patch("awa05.upload.github.ARCHIVOS", [archivo]), \
                 patch("awa05.upload.github.cargar_token") as cargar_token, \
                 patch("awa05.upload.github._github_repo") as github_repo, \
                 patch("builtins.print") as imprimir:
                subir_archivos(config)

        cargar_token.assert_not_called()
        github_repo.assert_not_called()
        self.assertIn("bloqueada", imprimir.call_args[0][0])

    def test_subir_dashboard_dry_run_no_pide_token(self):
        config = ConfigPublicacion(dry_run=True, dashboard_branch="data")

        with tempfile.TemporaryDirectory() as temporal:
            dashboard = Path(temporal) / "dashboard_data.json"
            dashboard.write_text('{"ok": true}', encoding="utf-8")
            with patch("awa05.upload.github.ruta_proyecto", return_value=dashboard), \
                 patch("awa05.upload.github.cargar_token") as cargar_token, \
                 patch("awa05.upload.github._github_repo") as github_repo:
                subir_dashboard(config)

        cargar_token.assert_not_called()
        github_repo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
