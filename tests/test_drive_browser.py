import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from helpers import drive_browser


class DriveBrowserAuthTests(unittest.TestCase):
    def test_service_account_credentials_preferred(self) -> None:
        payload = {"type": "service_account", "project_id": "demo"}
        with tempfile.TemporaryDirectory() as tmpdir:
            creds_path = Path(tmpdir) / "creds.json"
            token_path = Path(tmpdir) / "token.json"
            creds_path.write_text(json.dumps(payload), encoding="utf-8")

            dummy_credentials = MagicMock(name="ServiceAccountCreds")
            with (
                patch.object(drive_browser, "GOOGLE_CREDENTIALS_FILE", creds_path),
                patch.object(drive_browser, "GOOGLE_TOKEN_FILE", token_path),
                patch.object(drive_browser, "LEGACY_TOKEN_FILE", token_path.with_suffix(".pickle")),
                patch.object(drive_browser, "GOOGLE_IMPERSONATE_SUBJECT", None),
                patch(
                    "helpers.drive_browser.service_account.Credentials.from_service_account_info",
                    return_value=dummy_credentials,
                ) as from_info,
                patch("helpers.drive_browser.build", return_value="service") as build_mock,
            ):
                service = drive_browser.get_drive_service()

            self.assertEqual(service, "service")
            from_info.assert_called_once_with(payload, scopes=drive_browser.SCOPES)
            build_mock.assert_called_once_with(
                "drive", "v3", credentials=dummy_credentials, cache_discovery=False
            )

    def test_installed_app_flow_when_token_missing(self) -> None:
        oauth_payload = {"installed": {}}
        with tempfile.TemporaryDirectory() as tmpdir:
            creds_path = Path(tmpdir) / "client.json"
            token_path = Path(tmpdir) / "token.json"
            creds_path.write_text(json.dumps(oauth_payload), encoding="utf-8")

            generated_credentials = MagicMock(name="OAuthCreds")
            generated_credentials.to_json.return_value = "{}"
            with (
                patch.object(drive_browser, "GOOGLE_CREDENTIALS_FILE", creds_path),
                patch.object(drive_browser, "GOOGLE_TOKEN_FILE", token_path),
                patch.object(drive_browser, "LEGACY_TOKEN_FILE", token_path.with_suffix(".pickle")),
                patch.object(drive_browser, "GOOGLE_IMPERSONATE_SUBJECT", None),
                patch(
                    "helpers.drive_browser.Credentials.from_authorized_user_file",
                    side_effect=FileNotFoundError,
                ),
                patch(
                    "helpers.drive_browser.InstalledAppFlow.from_client_secrets_file"
                ) as flow_factory,
                patch("helpers.drive_browser.build", return_value="service") as build_mock,
            ):
                flow_instance = MagicMock()
                flow_instance.run_local_server.return_value = generated_credentials
                flow_factory.return_value = flow_instance

                service = drive_browser.get_drive_service()

            self.assertEqual(service, "service")
            flow_factory.assert_called_once_with(str(creds_path), drive_browser.SCOPES)
            flow_instance.run_local_server.assert_called_once()
            self.assertTrue(token_path.exists())
            self.assertEqual(token_path.read_text(encoding="utf-8"), "{}")
            build_mock.assert_called_once_with(
                "drive", "v3", credentials=generated_credentials, cache_discovery=False
            )


if __name__ == "__main__":
    unittest.main()
