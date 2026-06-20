"""
Shared HTTP helper for the OpenF1 API.
Docs: https://openf1.org/  (free, no auth required for historical data)
"""

import time
import requests

BASE_URL = "https://api.openf1.org/v1"


class OpenF1Error(Exception):
    """Raised when an OpenF1 request fails after retries."""


def fetch(endpoint: str, max_retries: int = 3, **params) -> list[dict]:
    """
    Call a single OpenF1 endpoint and return the parsed JSON list.

    Args:
        endpoint: e.g. "laps", "sessions", "pit", "stints", "weather".
        **params: query filters, e.g. session_key=9839, driver_number=1.
                  None values are dropped so we don't send empty filters.

    Returns:
        A list of dicts. OpenF1 always returns a JSON array, and an empty
        list is a normal, valid response (e.g. no team radio for a
        session) — callers should not treat [] as an error.
    """
    clean_params = {k: v for k, v in params.items() if v is not None}
    url = f"{BASE_URL}/{endpoint}"

    response = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=clean_params, timeout=15)
            if response.status_code == 429 and attempt < max_retries:
                time.sleep(2 ** attempt)  # OpenF1 rate-limits; back off and retry
                continue
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                raise OpenF1Error(f"OpenF1 request to '{endpoint}' failed: {e}") from e
            time.sleep(2 ** attempt)

    try:
        data = response.json()
    except ValueError as e:
        raise OpenF1Error(f"OpenF1 returned invalid JSON for '{endpoint}': {e}") from e

    if not isinstance(data, list):
        raise OpenF1Error(f"Unexpected response shape from '{endpoint}': {type(data)}")

    return data