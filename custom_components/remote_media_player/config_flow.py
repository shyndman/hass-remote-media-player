"""Config flow for Remote Media Player integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .api import ApiClientConnectionError, RemoteMediaPlayerClient
from .const import CONF_URL, DEFAULT_NAME, DOMAIN

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)


def _validate_url(url: str) -> str:
    """Validate WebSocket URL."""
    parsed = urlparse(url)
    if parsed.scheme not in ("ws", "wss"):
        msg = "URL must start with ws:// or wss://"
        raise vol.Invalid(msg)
    return url


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.URL,
            ),
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.TEXT,
            ),
        ),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Remote Media Player."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate URL format
                try:
                    _validate_url(user_input[CONF_URL])
                except vol.Invalid:
                    errors[CONF_URL] = "invalid_url"
                    return self.async_show_form(
                        step_id="user",
                        data_schema=STEP_USER_DATA_SCHEMA,
                        errors=errors,
                    )

                # Test connection
                client = RemoteMediaPlayerClient(
                    url=user_input[CONF_URL],
                )
                await client.connect()
                await client.get_state()  # Test the connection
                await client.disconnect()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )
            except ApiClientConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
