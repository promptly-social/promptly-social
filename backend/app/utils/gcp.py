import httpx
import google.auth
import google.oauth2.id_token
import google.oauth2.service_account
import logging
import traceback
from typing import Dict, Any
from google.auth.transport import requests as google_auth_requests

from app.core.config import settings

logger = logging.getLogger(__name__)


async def trigger_gcp_cloud_run(
    target_url: str,
    payload: Dict[str, Any],
    timeout: float = 300.0,
) -> httpx.Response:
    """
    Triggers a GCP Cloud Run service with an authenticated request.

    Args:
        target_url: The URL of the Cloud Run service to trigger.
        payload: The JSON payload to send to the service.
        timeout: The request timeout in seconds.

    Returns:
        The response from the Cloud Run service.

    Raises:
        Exception: If the request fails.
    """
    try:
        if not target_url:
            logger.error("Missing GCP Cloud Run function URL")
            raise ValueError("GCP Cloud Run function URL is not configured.")

        id_token = None
        auth_req = google_auth_requests.Request()

        if (
            settings.environment == "development"
            and settings.gcp_service_account_key_path
        ):
            logger.debug("Using service account key for GCP authentication.")
            try:
                creds = google.oauth2.service_account.IDTokenCredentials.from_service_account_file(
                    settings.gcp_service_account_key_path,
                    target_audience=target_url,
                )
                creds.refresh(auth_req)
                id_token = creds.token
            except FileNotFoundError:
                logger.error(
                    f"Service account key file not found at: {settings.gcp_service_account_key_path}"
                )
                raise
        else:
            logger.debug("Using default credentials for GCP authentication.")
            id_token = google.oauth2.id_token.fetch_id_token(auth_req, target_url)

        if not id_token:
            logger.error("Could not obtain GCP ID token.")
            raise Exception("Could not obtain GCP ID token.")

        headers = {"Authorization": f"Bearer {id_token}"}

        logger.info(
            f"Triggering GCP Cloud Run at {target_url}. This may take a few minutes..."
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                target_url,
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
        logger.info(f"Successfully triggered GCP Cloud Run at {target_url}")
        return response
    except httpx.ReadTimeout:
        logger.error(
            f"Timeout triggering GCP Cloud Run function at {target_url}. The function took too long to respond."
        )
        logger.error(traceback.format_exc())
        raise
    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error triggering GCP Cloud Run function at {target_url}: {e.response.status_code} - {e.response.text}"
        )
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"Error triggering GCP Cloud Run function at {target_url}: {e}")
        logger.error(traceback.format_exc())
        raise
