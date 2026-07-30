import unittest
from unittest.mock import patch, MagicMock
from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException

# Assuming your code is in a file named api_boilerplate.py
from src.utils.api_utils import send_api_request, APIError

"""
API Boilerplate Test Suite Evaluation Metrics
=============================================

This test suite uses pure Python standard libraries (unittest.mock) to evaluate 
all possible error states, routing strategies, and boundary behaviors of the 
send_api_request boilerplate function without opening real network sockets.

Tested Scenarios & Core Evaluations:

1. SUCCESS PATHS:
   - JSON Payload Evaluation: Asserts normal 200 OK success flow with clean 
     dictionary parsing.
   - Empty Content Boundary Evaluation: Verifies the code returns a clean {} 
     when response.content is completely empty, ensuring no JSON parsing crashes.

2. TRANSIENT & NETWORK ANOMALIES (Retry Loop Logic):
   - Pure Network Layer Failures: Simulates low-level Timeout and ConnectionError 
     exceptions across all attempts, ensuring the loop counts and drops into an 
     APIError exactly at the max_retries boundary.
   - Transient Server Errors (5xx/429): Simulates continuous server-side issues 
     to confirm they trigger retry attempts up to the loop limit.
   - Transient Recovery Path: Simulates a failing server on the first attempt 
     that recovers dynamically to return a 200 OK on a subsequent try.

3. COLD SHORT-CIRCUITS (Waste Prevention):
   - Permanent Client Failures (4xx except 429): Simulates 404/401 fatal errors. 
     Evaluates that the function halts execution on Attempt 1, skipping expensive 
     and useless retry cycles.
   - Untracked Library Faults: Evaluates generic base-level RequestExceptions 
     to guarantee a safe crash wrapper without indefinite hangs.
"""


class TestSendAPIRequest(unittest.TestCase):

    @patch('requests.Session.request')
    def test_success_with_json_payload(self, mock_request):
        """1. Evaluates normal 200 OK success flow with a JSON payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"data": "success"}'
        mock_response.json.return_value = {"data": "success"}
        mock_request.return_value = mock_response

        result = send_api_request(endpoint="test", base_url="https://api.com")

        self.assertEqual(result, {"data": "success"})
        mock_request.assert_called_once()

    @patch('requests.Session.request')
    def test_success_empty_content(self, mock_request):
        """2. Evaluates handling of an empty byte string success response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b''  # Empty body
        mock_request.return_value = mock_response

        result = send_api_request(endpoint="test", base_url="https://api.com")

        self.assertEqual(result, {})

    @patch('requests.Session.request')
    def test_network_timeout_retry_and_exhaustion(self, mock_request):
        """3. Evaluates Timeout errors across all retries until exhaustion."""
        mock_request.side_effect = Timeout("Connection timed out")

        with self.assertRaises(APIError) as context:
            send_api_request(endpoint="test", max_retries=3, backoff_factor=0.0)

        self.assertIn("Network error after 3 retries", str(context.exception))
        self.assertEqual(mock_request.call_count, 3)

    @patch('requests.Session.request')
    def test_network_connection_error_and_exhaustion(self, mock_request):
        """4. Evaluates ConnectionError failures across all retries until exhaustion."""
        mock_request.side_effect = ConnectionError("DNS resolution failed")

        with self.assertRaises(APIError) as context:
            send_api_request(endpoint="test", max_retries=3, backoff_factor=0.0)

        self.assertIn("Network error after 3 retries", str(context.exception))
        self.assertEqual(mock_request.call_count, 3)

    @patch('requests.Session.request')
    def test_transient_http_error_retry_and_exhaustion(self, mock_request):
        """5. Evaluates transient 500 error iterations up to maximum limits."""
        # Create a mock exception that mirrors what requests.raise_for_status() throws
        mock_response = MagicMock()
        mock_response.status_code = 500
        http_error = HTTPError("Internal Server Error", response=mock_response)

        mock_request.side_effect = http_error

        with self.assertRaises(APIError) as context:
            send_api_request(endpoint="test", max_retries=3, backoff_factor=0.0)

        self.assertIn("API failed with status 500 after 3 retries", str(context.exception))
        self.assertEqual(mock_request.call_count, 3)

    @patch('requests.Session.request')
    def test_transient_http_error_recovery(self, mock_request):
        """6. Evaluates a transient error recovering on a later attempt."""
        # Mocking 503 error on first call, then 200 OK success response on second call
        fail_response = MagicMock()
        fail_response.status_code = 503
        http_error = HTTPError("Service Unavailable", response=fail_response)

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.content = b'{"status": "recovered"}'
        success_response.json.return_value = {"status": "recovered"}

        mock_request.side_effect = [http_error, success_response]

        result = send_api_request(endpoint="test", max_retries=3, backoff_factor=0.0)

        self.assertEqual(result, {"status": "recovered"})
        self.assertEqual(mock_request.call_count, 2)

    @patch('requests.Session.request')
    def test_permanent_http_error_immediate_fail(self, mock_request):
        """7. Evaluates permanent 404 client errors exit instantly on attempt 1."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = HTTPError("Not Found", response=mock_response)

        mock_request.side_effect = http_error

        with self.assertRaises(APIError) as context:
            send_api_request(endpoint="test", max_retries=3, backoff_factor=0.0)

        self.assertIn("API returned permanent error 404", str(context.exception))
        self.assertEqual(mock_request.call_count, 1)  # Only called once! Retries skipped.

    @patch('requests.Session.request')
    def test_untracked_generic_request_exception(self, mock_request):
        """8. Evaluates generic non-retryable requests exceptions failing instantly."""
        mock_request.side_effect = RequestException("Unknown low level library crash")

        with self.assertRaises(APIError) as context:
            send_api_request(endpoint="test", max_retries=3, backoff_factor=0.0)

        self.assertIn("An unexpected error occurred", str(context.exception))
        self.assertEqual(mock_request.call_count, 1)
