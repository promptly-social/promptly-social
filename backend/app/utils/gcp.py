import json
import logging
from typing import Any, Dict, Optional

import google.auth
import google.auth.transport.requests
import httpx
import google.oauth2.id_token
import google.oauth2.service_account
from google.auth import compute_engine
from google.auth.transport import requests as google_auth_requests
from google.auth import exceptions

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_id_token(target_url: str) -> Optional[str]:
    """
    Try multiple methods to get a valid ID token for the target URL.

    Order of attempts:
    1. Service account key file (if configured in settings)
    2. Application Default Credentials (ADC)
    3. Compute Engine credentials (for GCP environments)
    4. Development token (if explicitly allowed in settings)

    Returns:
        str: ID token if successful, None otherwise
    """
    auth_req = google_auth_requests.Request()

    # 1. Try service account key file (for local development)
    if settings.environment == "development" and settings.gcp_service_account_key_path:
        try:
            logger.debug(
                "Attempting to use service account key file for authentication"
            )
            creds = google.oauth2.service_account.IDTokenCredentials.from_service_account_file(
                settings.gcp_service_account_key_path,
                target_audience=target_url,
            )
            creds.refresh(auth_req)
            return creds.token
        except Exception as e:
            logger.warning(f"Service account key authentication failed: {e}")

    # 2. Try Application Default Credentials (ADC)
    try:
        logger.debug("Attempting to use Application Default Credentials")
        creds, _ = google.auth.default()
        creds.refresh(auth_req)

        # For service accounts, we need to create an ID token
        if hasattr(creds, "service_account_email"):
            creds = google.oauth2.id_token.IDTokenCredentials(
                auth_req,
                None,
                service_account_email=creds.service_account_email,
                token_uri=creds.token_uri,
                target_audience=target_url,
            )
            creds.refresh(auth_req)
            return creds.token
    except Exception as e:
        logger.warning(f"Application Default Credentials failed: {e}")

    # 3. Try Compute Engine credentials (for GCP environments)
    try:
        logger.debug("Attempting to use Compute Engine credentials")
        creds = compute_engine.IDTokenCredentials(
            auth_req, target_audience=target_url, use_metadata_identity_endpoint=True
        )
        creds.refresh(auth_req)
        return creds.token
    except Exception as e:
        logger.warning(f"Compute Engine credentials failed: {e}")

    raise RuntimeError(
        "No valid authentication method could be found. "
        "Please ensure you have proper GCP credentials configured for local development.\n"
        "1. Set GOOGLE_APPLICATION_CREDENTIALS to point to a service account key file\n"
        "2. Or run `gcloud auth application-default login` to use your user credentials"
    )


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

        # Get ID token for authentication
        # Fetch an ID token using Google helper; this allows tests to patch fetch_id_token.
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2.id_token import fetch_id_token

        try:
            id_token = fetch_id_token(GoogleRequest(), target_url)
        except exceptions.DefaultCredentialsError as cred_err:
            # Fallback to legacy multi-strategy helper for local development where
            # ADC or metadata server may not be available.
            logger.warning(
                "fetch_id_token failed using ADC/metadata credentials; falling back to get_id_token helper: %s",
                cred_err,
            )
            id_token = get_id_token(target_url)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {id_token}",
        }

        logger.info(
            f"Triggering GCP Cloud Run at {target_url}. This may take a few minutes..."
        )
        # Make the request
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    target_url, json=payload, headers=headers, timeout=timeout
                )
                response.raise_for_status()
                return response

        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP error {e.response.status_code}"
            if e.response.text:
                try:
                    error_data = e.response.json()
                    error_detail = (
                        f"{error_detail}: {error_data.get('detail', e.response.text)}"
                    )
                except (json.JSONDecodeError, AttributeError):
                    error_detail = f"{error_detail}: {e.response.text}"

            logger.error(f"Error triggering Cloud Run: {error_detail}")
            logger.debug(f"Request headers: {headers}")
            logger.debug(f"Response headers: {e.response.headers}")

            # For 401/403 errors, include auth troubleshooting info
            if e.response.status_code in (401, 403):
                logger.error(
                    "Authentication failed. Please check that:\n"
                    "1. Your service account has the necessary IAM permissions\n"
                    "2. The target Cloud Run service allows unauthenticated invocations if needed\n"
                    "3. The service account email is added as a member with the 'roles/run.invoker' role"
                )

            raise RuntimeError(f"Failed to trigger Cloud Run: {error_detail}") from e

        except Exception as e:
            logger.error(
                f"Unexpected error triggering Cloud Run: {str(e)}", exc_info=True
            )
            raise RuntimeError(f"Failed to trigger Cloud Run: {str(e)}") from e

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error triggering GCP Cloud Run function at {target_url}: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except httpx.ReadTimeout as e:
        error_msg = f"Timeout triggering GCP Cloud Run function at {target_url}. The function took too long to respond."
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f"Error triggering GCP Cloud Run function at {target_url}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e
