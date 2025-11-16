"""Tests for logging utilities."""

import logging
from unittest.mock import MagicMock, patch

from ingestion.utils.logging import get_logger, setup_logging


class TestSetupLogging:
    """Test setup_logging function."""

    @patch("ingestion.utils.logging.logging.basicConfig")
    def test_setup_logging_default(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with default parameters."""
        setup_logging()

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.INFO
        assert "%(asctime)s" in call_kwargs["format"]
        assert "%(levelname)s" in call_kwargs["format"]
        assert len(call_kwargs["handlers"]) == 1

    @patch("ingestion.utils.logging.logging.basicConfig")
    def test_setup_logging_debug_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with DEBUG level."""
        setup_logging(level="DEBUG")

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.DEBUG

    @patch("ingestion.utils.logging.logging.basicConfig")
    def test_setup_logging_warning_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with WARNING level."""
        setup_logging(level="WARNING")

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.WARNING

    @patch("ingestion.utils.logging.logging.basicConfig")
    def test_setup_logging_error_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with ERROR level."""
        setup_logging(level="ERROR")

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.ERROR

    @patch("ingestion.utils.logging.logging.basicConfig")
    def test_setup_logging_critical_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with CRITICAL level."""
        setup_logging(level="CRITICAL")

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.CRITICAL

    @patch("ingestion.utils.logging.logging.basicConfig")
    def test_setup_logging_lowercase_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging converts lowercase level to uppercase."""
        setup_logging(level="info")

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.INFO

    @patch("ingestion.utils.logging.logging.basicConfig")
    def test_setup_logging_custom_format(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with custom format string."""
        custom_format = "%(levelname)s: %(message)s"
        setup_logging(format_string=custom_format)

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["format"] == custom_format

    @patch("ingestion.utils.logging.logging.basicConfig")
    def test_setup_logging_with_both_params(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with both level and format customized."""
        custom_format = "%(name)s - %(message)s"
        setup_logging(level="ERROR", format_string=custom_format)

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.ERROR
        assert call_kwargs["format"] == custom_format


class TestGetLogger:
    """Test get_logger function."""

    @patch("ingestion.utils.logging.logging.getLogger")
    def test_get_logger(self, mock_get_logger: MagicMock) -> None:
        """Test get_logger returns logger instance."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test_module")

        mock_get_logger.assert_called_once_with("test_module")
        assert logger is mock_logger

    @patch("ingestion.utils.logging.logging.getLogger")
    def test_get_logger_with_different_names(self, mock_get_logger: MagicMock) -> None:
        """Test get_logger with different module names."""
        logger_name = "ingestion.sources.rest_api"
        get_logger(logger_name)

        mock_get_logger.assert_called_once_with(logger_name)
