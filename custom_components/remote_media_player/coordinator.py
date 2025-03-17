"""DataUpdateCoordinator for Remote Media Player."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiClientConnectionError, RemoteMediaPlayerClient
from .const import CONF_URL, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class RemoteMediaPlayerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the Remote Media Player."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=None,  # We'll get updates via WebSocket
        )

        self.client = RemoteMediaPlayerClient(
            url=entry.data[CONF_URL],
        )
        self.client.set_state_callback(self._handle_state_update)
        self.client.set_error_callback(self._handle_error)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            return await self.client.get_state()
        except ApiClientConnectionError as err:
            msg = f"Error communicating with API: {err}"
            raise UpdateFailed(msg) from err

    def _handle_state_update(self, state: dict[str, Any]) -> None:
        """Handle state update from WebSocket."""
        self.async_set_updated_data(state)

    def _handle_error(self, error: str) -> None:
        """Handle error from WebSocket."""
        _LOGGER.error("Error from media player: %s", error)
        self.last_update_success = False

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            await self.client.connect()
            await self.async_refresh()
        except ApiClientConnectionError as err:
            msg = f"Failed to connect to media player: {err}"
            raise ConfigEntryNotReady(msg) from err
