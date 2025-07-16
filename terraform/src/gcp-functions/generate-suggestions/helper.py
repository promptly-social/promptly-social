import json
from typing import Any, Dict
from datetime import datetime, timezone

import logging

logger = logging.getLogger(__name__)


def extract_json_from_llm_response(response: str) -> Dict[str, Any]:
    """Extract JSON from LLM response."""
    try:
        # Remove any markdown formatting
        response = response.replace("```json", "").replace("```", "")
        return json.loads(response)
    except Exception as e:
        logger.error(f"Error extracting JSON from response: {e}")
        return {}


def parse_date_to_utc(date_string: str) -> str:
    """
    Parse date string to UTC format.
    Handles various date formats and returns ISO format UTC string.
    """
    if not date_string:
        return ""

    try:
        # Common date formats to try
        date_formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
            "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO format with microseconds and timezone offset
            "%Y-%m-%dT%H:%M:%S.%f",  # ISO format with microseconds without Z
            "%Y-%m-%dT%H:%M:%SZ",  # ISO format
            "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone offset
            "%Y-%m-%dT%H:%M:%S",  # ISO format without Z
            "%Y-%m-%d %H:%M:%S",  # Standard datetime
            "%Y-%m-%d",  # Date only
            "%B %d, %Y",  # Month DD, YYYY
            "%d %B %Y",  # DD Month YYYY
        ]

        parsed_date = None
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date_string.strip(), date_format)
                break
            except ValueError:
                continue

        if parsed_date:
            # Convert to UTC ISO format
            if parsed_date.tzinfo is not None:
                # Convert timezone-aware datetime to UTC
                utc_date = parsed_date.astimezone(timezone.utc)
            else:
                # Assume naive datetime is UTC
                utc_date = parsed_date.replace(tzinfo=timezone.utc)

            return utc_date.isoformat()
        else:
            # If we can't parse it, return the original string
            logger.warning(f"Could not parse date format: {date_string}")
            return date_string

    except Exception as e:
        logger.error(f"Error parsing date '{date_string}': {str(e)}")
        return date_string
