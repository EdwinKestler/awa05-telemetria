import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from awa05.upload.github import (
    ConfigPublicacion,
    _ejecutar_con_reintentos,
    config_desde_env,
    subir_archivos,
    subir_dashboard,
)


class UploadGithubTests(unittest.TestCase):
    def test_subir_archivos_dry_run_no_pide_token_ni_cliente(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = Path(temporal) / "nivel_raw.csv"
            archivo.write_text("timestamp,volumen_litros\n2026-01-01,1.0\n", encoding="utf-8")
            config = ConfigPublicacion(dry_run=True, data_branch="data")

            with patch("awa05.upload.github.ARCHIVOS", [archivo]), \
                 patch("awa05.upload.github.cargar_token") as cargar_token, \
                 patch("awa05.upload.github._github_repo") as github_repo, \
                 patch("awa05.upload.github._ejecutar_con_reintentos") as reintentos:
                subir_archivos(config)

        cargar_token.assert_not_called()
        github_repo.assert_not_called()
        reintentos.assert_not_called()

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

    def test_config_desde_env_incluye_reintentos_de_upload(self):
        with patch.dict(
            "os.environ",
            {
                "AWA05_DRY_RUN": "true",
                "AWA05_UPLOAD_RETRIES": "4",
                "AWA05_UPLOAD_RETRY_DELAY_S": "0.25",
            },
            clear=True,
        ):
            config = config_desde_env()

        self.assertTrue(config.dry_run)
        self.assertEqual(config.upload_retries, 4)
        self.assertEqual(config.upload_retry_delay_s, 0.25)

    def test_ejecutar_con_reintentos_reintenta_y_devuelve_resultado(self):
        intentos = []
        dormir = Mock()

        def operacion():
            intentos.append("intento")
            if len(intentos) == 1:
                raise RuntimeError("fallo temporal")
            return "ok"

        resultado = _ejecutar_con_reintentos(
            "publicar prueba",
            operacion,
            retries=2,
            delay_s=0.1,
            sleep_fn=dormir,
        )

        self.assertEqual(resultado, "ok")
        self.assertEqual(intentos, ["intento", "intento"])
        dormir.assert_called_once_with(0.1)

    def test_ejecutar_con_reintentos_relanza_al_agotar_intentos(self):
        dormir = Mock()

        with self.assertRaisesRegex(RuntimeError, "permanente"):
            _ejecutar_con_reintentos(
                "publicar prueba",
                lambda: (_ for _ in ()).throw(RuntimeError("permanente")),
                retries=1,
                delay_s=0,
                sleep_fn=dormir,
            )

        dormir.assert_not_called()

    def test_subir_dashboard_usa_reintentos_para_publicacion_real(self):
        config = ConfigPublicacion(
            dry_run=False,
            dashboard_branch="data",
            upload_retries=3,
            upload_retry_delay_s=0,
        )
        repo = Mock()

        with tempfile.TemporaryDirectory() as temporal:
            dashboard = Path(temporal) / "dashboard_data.json"
            dashboard.write_text('{"ok": true}', encoding="utf-8")
            with patch("awa05.upload.github.ruta_proyecto", return_value=dashboard), \
                 patch("awa05.upload.github.cargar_token", return_value="token"), \
                 patch("awa05.upload.github._github_repo", return_value=repo), \
                 patch("awa05.upload.github._asegurar_branch") as asegurar_branch, \
                 patch("awa05.upload.github._publicar_archivo") as publicar:
                subir_dashboard(config)

        asegurar_branch.assert_called_once()
        publicar.assert_called_once()


if __name__ == "__main__":
    unittest.main()
