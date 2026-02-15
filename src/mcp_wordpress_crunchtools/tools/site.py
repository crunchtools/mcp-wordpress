"""Site management tools.

Tools for getting WordPress site information and testing connectivity.
"""

import logging
from typing import Any

from ..client import get_client
from ..config import get_config

logger = logging.getLogger(__name__)


async def get_site_info() -> dict[str, Any]:
    """Get WordPress site information.

    Returns:
        Dictionary containing site title, description, URL, timezone, etc.
    """
    client = get_client()
    config = get_config()

    # Try to get settings from WordPress REST API
    try:
        settings_response = await client.get("/settings")

        if isinstance(settings_response, dict):
            return {
                "site": {
                    "title": settings_response.get("title", "Unknown"),
                    "description": settings_response.get("description", ""),
                    "url": settings_response.get("url", config.base_url),
                    "email": settings_response.get("email", ""),
                    "timezone": settings_response.get("timezone_string", "UTC"),
                    "date_format": settings_response.get("date_format", ""),
                    "time_format": settings_response.get("time_format", ""),
                    "language": settings_response.get("language", "en_US"),
                }
            }
    except Exception as e:
        # Settings endpoint may require admin privileges
        logger.debug("Could not fetch site settings: %s", e)

    # Fallback: return basic info from config
    return {
        "site": {
            "url": config.base_url,
            "api_url": config.api_base_url,
            "note": "Full site info requires Settings API access",
        }
    }


async def test_connection() -> dict[str, Any]:
    """Test connection to WordPress REST API.

    Verifies that the API credentials work by making a simple request.

    Returns:
        Dictionary with connection status and details
    """
    client = get_client()
    config = get_config()

    try:
        # Try to get current user to verify authentication
        response = await client.get("/users/me")
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {e}",
            "site_url": config.base_url,
        }

    if isinstance(response, dict):
        return {
            "success": True,
            "message": "Successfully connected to WordPress",
            "site_url": config.base_url,
            "authenticated_as": response.get("name", response.get("slug", "Unknown")),
            "user_id": response.get("id"),
            "capabilities": list(response.get("capabilities", {}).keys())[:10],
        }

    return {
        "success": True,
        "message": "Connected but unexpected response format",
        "site_url": config.base_url,
    }
