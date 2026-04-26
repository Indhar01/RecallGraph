"""Tests for Notion authentication helpers."""

import pytest
from unittest.mock import patch, MagicMock

# Skip all tests in this module if notion-client is not installed
pytest.importorskip("notion_client", reason="notion-client package not installed")

from memograph.integrations.notion.auth import NotionAuth


class TestNotionAuth:
    """Test NotionAuth helper methods."""

    def test_get_auth_url_basic(self):
        """Test generating OAuth authorization URL."""
        url = NotionAuth.get_auth_url(
            client_id="test_client_id", redirect_uri="https://example.com/callback"
        )

        assert "https://api.notion.com/v1/oauth/authorize" in url
        assert "client_id=test_client_id" in url
        assert "redirect_uri=https://example.com/callback" in url
        assert "response_type=code" in url

    def test_get_auth_url_with_state(self):
        """Test OAuth URL with state parameter."""
        url = NotionAuth.get_auth_url(
            client_id="test_id",
            redirect_uri="https://example.com/callback",
            state="random_state_123",
        )

        assert "state=random_state_123" in url

    @patch("memograph.integrations.notion.auth.requests.post")
    def test_exchange_code_success(self, mock_post):
        """Test successful OAuth code exchange."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "secret_token_123",
            "bot_id": "bot_123",
            "workspace_id": "ws_123",
            "workspace_name": "My Workspace",
        }
        mock_post.return_value = mock_response

        result = NotionAuth.exchange_code(
            code="auth_code_123",
            client_id="client_id",
            client_secret="client_secret",
            redirect_uri="https://example.com/callback",
        )

        assert result["access_token"] == "secret_token_123"
        assert result["bot_id"] == "bot_123"
        mock_post.assert_called_once()

    @patch("memograph.integrations.notion.auth.requests.post")
    def test_exchange_code_failure(self, mock_post):
        """Test OAuth code exchange failure."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid code"
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="OAuth token exchange failed"):
            NotionAuth.exchange_code(
                code="invalid_code",
                client_id="client_id",
                client_secret="client_secret",
                redirect_uri="https://example.com/callback",
            )

    def test_save_token(self, tmp_path):
        """Test saving token to file."""
        token_file = tmp_path / "test_token"
        NotionAuth.save_token("secret_test_token", str(token_file))

        assert token_file.exists()
        assert token_file.read_text() == "secret_test_token"

    def test_load_token_exists(self, tmp_path):
        """Test loading token from existing file."""
        token_file = tmp_path / "test_token"
        token_file.write_text("secret_loaded_token")

        token = NotionAuth.load_token(str(token_file))
        assert token == "secret_loaded_token"

    def test_load_token_not_exists(self, tmp_path):
        """Test loading token from non-existent file."""
        token_file = tmp_path / "nonexistent_token"
        token = NotionAuth.load_token(str(token_file))
        assert token is None

    def test_save_config(self, tmp_path):
        """Test saving configuration to JSON file."""
        config_file = tmp_path / "test_config.json"
        config = {
            "access_token": "secret_token",
            "workspace_id": "ws_123",
            "workspace_name": "Test Workspace",
        }

        NotionAuth.save_config(config, str(config_file))

        assert config_file.exists()
        import json

        loaded = json.loads(config_file.read_text())
        assert loaded["access_token"] == "secret_token"
        assert loaded["workspace_id"] == "ws_123"

    def test_load_config_exists(self, tmp_path):
        """Test loading configuration from existing file."""
        config_file = tmp_path / "test_config.json"
        import json

        config_file.write_text(
            json.dumps({"access_token": "secret_token", "workspace_id": "ws_123"})
        )

        config = NotionAuth.load_config(str(config_file))
        assert config["access_token"] == "secret_token"
        assert config["workspace_id"] == "ws_123"

    def test_load_config_not_exists(self, tmp_path):
        """Test loading configuration from non-existent file."""
        config_file = tmp_path / "nonexistent_config.json"
        config = NotionAuth.load_config(str(config_file))
        assert config is None

    def test_get_token_from_env(self, monkeypatch):
        """Test getting token from environment variable."""
        monkeypatch.setenv("NOTION_API_TOKEN", "env_token_123")
        token = NotionAuth.get_token_from_env()
        assert token == "env_token_123"

    def test_get_token_from_env_alternative(self, monkeypatch):
        """Test getting token from alternative env var."""
        monkeypatch.delenv("NOTION_API_TOKEN", raising=False)
        monkeypatch.setenv("NOTION_TOKEN", "alt_token_123")
        token = NotionAuth.get_token_from_env()
        assert token == "alt_token_123"

    def test_get_token_from_env_none(self, monkeypatch):
        """Test getting token when no env var set."""
        monkeypatch.delenv("NOTION_API_TOKEN", raising=False)
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        token = NotionAuth.get_token_from_env()
        assert token is None

    def test_get_token_priority_explicit(self, tmp_path, monkeypatch):
        """Test that explicit token has highest priority."""
        # Set up all other sources
        monkeypatch.setenv("NOTION_API_TOKEN", "env_token")
        token_file = tmp_path / "token"
        token_file.write_text("file_token")

        token = NotionAuth.get_token(
            token="explicit_token", config_file=str(token_file)
        )
        assert token == "explicit_token"

    def test_get_token_priority_env(self, tmp_path, monkeypatch):
        """Test that env var has second priority."""
        monkeypatch.setenv("NOTION_API_TOKEN", "env_token")
        token_file = tmp_path / "token"
        token_file.write_text("file_token")

        token = NotionAuth.get_token(config_file=str(token_file))
        assert token == "env_token"

    def test_get_token_priority_file(self, tmp_path, monkeypatch):
        """Test that file token has third priority."""
        monkeypatch.delenv("NOTION_API_TOKEN", raising=False)
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        token_file = tmp_path / "token"
        token_file.write_text("file_token")

        token = NotionAuth.get_token(config_file=str(token_file))
        assert token == "file_token"

    def test_validate_token_format_valid_secret(self):
        """Test validating secret_ token format."""
        assert NotionAuth.validate_token_format("secret_abc123") is True

    def test_validate_token_format_valid_ntn(self):
        """Test validating ntn_ token format."""
        assert NotionAuth.validate_token_format("ntn_xyz789") is True

    def test_validate_token_format_invalid(self):
        """Test validating invalid token format."""
        assert NotionAuth.validate_token_format("invalid_token") is False
        assert NotionAuth.validate_token_format("") is False
        assert NotionAuth.validate_token_format(None) is False

    @patch("builtins.input")
    def test_setup_integration_interactive_valid(
        self, mock_input, tmp_path, monkeypatch
    ):
        """Test interactive setup with valid token."""
        mock_input.return_value = "secret_valid_token"
        monkeypatch.chdir(tmp_path)

        token = NotionAuth.setup_integration_interactive()

        assert token == "secret_valid_token"
        assert (tmp_path / NotionAuth.DEFAULT_TOKEN_FILE).exists()

    @patch("builtins.input")
    def test_setup_integration_interactive_empty(self, mock_input):
        """Test interactive setup with empty token."""
        mock_input.return_value = ""

        with pytest.raises(ValueError, match="No token provided"):
            NotionAuth.setup_integration_interactive()

    @patch("builtins.input")
    def test_setup_integration_interactive_invalid_cancelled(self, mock_input):
        """Test interactive setup with invalid token (user cancels)."""
        mock_input.side_effect = ["invalid_format", "n"]

        with pytest.raises(ValueError, match="Setup cancelled"):
            NotionAuth.setup_integration_interactive()
