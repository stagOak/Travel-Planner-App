from unittest.mock import patch, MagicMock
import pytest
import requests

from src.travel_planner.travel_planner import get_destination_weather


@patch('requests.get')
def test_weather_timeout(mock_get, capsys):
    """Tests that a Timeout exception is caught and printed."""
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    result = get_destination_weather("New York")

    assert result is None
    captured = capsys.readouterr()
    # Updated to match your exact code string
    assert "requests.exceptions.Timeout - timeout_err:" in captured.out


@patch('requests.get')
def test_weather_http_error(mock_get, capsys):
    """Tests that an HTTPError (like a 404 or 500) is caught and printed."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    mock_get.return_value = mock_response

    result = get_destination_weather("London")

    assert result is None
    captured = capsys.readouterr()
    # Updated to match your exact code string (including the typo 'hrequests')
    assert "hrequests.exceptions.HTTPError - http_err:" in captured.out


@patch('requests.get')
def test_weather_connection_error(mock_get, capsys):
    """Tests that a ConnectionError (network down) is caught and printed."""
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

    result = get_destination_weather("Paris")

    assert result is None
    captured = capsys.readouterr()
    # Updated to match your exact code string
    assert "requests.exceptions.ConnectionError - connection_err:" in captured.out


@patch('requests.get')
def test_weather_request_exception(mock_get, capsys):
    """Tests that any generic requests exception is caught and printed."""
    mock_get.side_effect = requests.exceptions.RequestException("Unknown requests library error")

    result = get_destination_weather("Berlin")

    assert result is None
    captured = capsys.readouterr()
    # Updated to match your exact code string
    assert "requests.exceptions.RequestException - req_exp:" in captured.out


@patch('requests.get')
def test_weather_generic_exception_exits(mock_get):
    """Tests that any unexpected generic code exception forces a sys.exit."""
    mock_get.side_effect = Exception("System corruption")

    with pytest.raises(SystemExit) as exc_info:
        get_destination_weather("Tokyo")

    # Updated to match your exact sys.exit string
    assert "internal Python runtime bugs - e:" in str(exc_info.value)
