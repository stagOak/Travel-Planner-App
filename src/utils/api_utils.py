import logging
import time
from typing import Any, Dict, Optional
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
HTTP STATUS CODE & EXCEPTION REFERENCE

4xx Client Errors (Throws HTTPError via raise_for_status)
-------------------------------------------------------
400 Bad Request: Malformed data or syntax error.
401 Unauthorized: Authentication is missing or invalid.
403 Forbidden: Valid credentials, but lacks permission.
404 Not Found: Resource does not exist on the server.
405 Method Not Allowed: HTTP method (e.g. POST) not supported.
408 Request Timeout: Client took too long to send request.
409 Conflict: Request conflicts with current server state.
422 Unprocessable Entity: Valid syntax, but semantic errors.
429 Too Many Requests: Rate limit exceeded.

5xx Server Errors (Throws HTTPError via raise_for_status)
-------------------------------------------------------
500 Internal Server Error: Server crashed or encountered a bug.
502 Bad Gateway: Upstream server returned an invalid response.
503 Service Unavailable: Server overloaded or down for maintenance.
504 Gateway Timeout: Upstream server failed to respond in time.

Network & Protocol Failures (Throws specific exceptions, no status codes)
-----------------------------------------------------------------------
ConnectionError: DNS failure, firewall block, or refused port connection.
ConnectTimeout: Server took too long to accept the initial connection.
ReadTimeout: Server accepted connection but stopped sending data mid-way.
TooManyRedirects: URL trapped in an infinite redirect loop.
"""


class APIError(Exception):
    """Base custom exception for API failures."""
    pass


def send_api_request(
        endpoint: str,
        method: str = "GET",
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 5,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        **kwargs
) -> Dict[str, Any] | None:
    """
    A standalone function to handle HTTP requests with automatic retries,
    exponential backoff, and standardized exception handling.
    """
    # Build the full URL smoothly
    if base_url:
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    else:
        url = endpoint

    # Use a session context manager to keep connection pooling efficient
    with requests.Session() as session:

        if headers:
            session.headers.update(headers)

        for attempt in range(1, max_retries + 1):
            try:
                response = session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    timeout=timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response.json() if response.content else {}

            except (Timeout, ConnectionError) as e:
                logger.warning(f"Attempt {attempt}/{max_retries} failed due to network issue: {e}")
                if attempt == max_retries:
                    raise APIError(f"Network error after {max_retries} retries: {e}") from e

            except HTTPError as e:
                status_code = e.response.status_code if e.response else 500
                transient_statuses = {429, 500, 502, 503, 504}

                if status_code in transient_statuses:
                    logger.warning(f"Attempt {attempt}/{max_retries} failed with status {status_code}.")
                    if attempt == max_retries:
                        raise APIError(f"API failed with status {status_code} after {max_retries} retries.") from e
                else:
                    logger.error(f"Permanent HTTP error {status_code} for {url}. Skipping retries.")
                    raise APIError(f"API returned permanent error {status_code}: {e}") from e

            except RequestException as e:
                logger.error(f"Non-retryable request error: {e}")
                raise APIError(f"An unexpected error occurred: {e}") from e

            # Wait with exponential backoff before the next attempt
            sleep_time = backoff_factor * (2 ** (attempt - 1))
            logger.info(f"Sleeping for {sleep_time} seconds before next retry...")
            time.sleep(sleep_time)


if __name__ == "__main__":
    """
    This code demonstrates the use of the send_api_request() function when no key is required.
    use without API key: python api_utils.py Seattle https://geocoding-api.open-meteo.com/v1/search
    when using a key add it to the params
    """

    # initialize the argument parser
    parser = argparse.ArgumentParser()

    # add parameters to the argument parser
    parser.add_argument("destination", type=str, help="travel destination")
    parser.add_argument("endpoint", type=str, help="url for api endpoint")
    parser.add_argument("-v", "--verbose", action="store_true", help="Toggle verbose mode (Flag)")

    # parse the arguments from the terminal
    args = parser.parse_args()

    # begin processing
    if args.verbose:
        print("\nopen meteo is being queried for coordinates for {}...".format(args.destination))

    params_ = {
        "name": args.destination,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    response_json = send_api_request(
        endpoint=args.endpoint,
        method="GET",
        # base_url=None,
        # headers=None,
        params=params_,
        # json_data=None,
        timeout=5,
        max_retries=3,
        backoff_factor=2.0,
        # ** kwargs
    )

    print(response_json)
