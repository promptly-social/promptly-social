import json
from typing import Any, Dict

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
