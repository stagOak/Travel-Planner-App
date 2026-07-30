import logging
import time
from typing import Any, Dict, Optional
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
