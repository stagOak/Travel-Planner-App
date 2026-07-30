import requests
from unittest.mock import patch

from src.travel_planner import open_metro_weather as bw
from src.travel_planner.wttr_in_weather import get_destination_weather


def test_get_destination_weather_timeout(monkeypatch):
    """Test that requests.exceptions.Timeout triggers the backup weather function."""
    destination = "New York"

    with patch("requests.get", side_effect=requests.exceptions.Timeout("Connection timed out")):
        monkeypatch.setattr(bw, "get_backup_weather", lambda dest: f"Backup weather for {dest}")

        result = get_destination_weather(destination)
        assert result == "Backup weather for New York"


def test_get_destination_weather_http_error(monkeypatch):
    """Test that requests.exceptions.HTTPError (e.g., 500) triggers backup."""
    destination = "London"

    with patch("requests.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")

        monkeypatch.setattr(bw, "get_backup_weather", lambda dest: f"Backup weather for {dest}")

        result = get_destination_weather(destination)
        assert result == "Backup weather for London"


def test_get_destination_weather_connection_error(monkeypatch):
    """Test that requests.exceptions.ConnectionError triggers the backup weather function."""
    destination = "Paris"

    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Failed to connect")):
        monkeypatch.setattr(bw, "get_backup_weather", lambda dest: f"Backup weather for {dest}")

        result = get_destination_weather(destination)
        assert result == "Backup weather for Paris"


def test_get_destination_weather_request_exception(monkeypatch):
    """Test the final catch-all requests.exceptions.RequestException block."""
    destination = "Tokyo"

    with patch("requests.get", side_effect=requests.exceptions.RequestException("Generic request error")):
        monkeypatch.setattr(bw, "get_backup_weather", lambda dest: f"Backup weather for {dest}")

        result = get_destination_weather(destination)
        assert result == "Backup weather for Tokyo"
