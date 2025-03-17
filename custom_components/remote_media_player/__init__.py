"""
Custom integration to integrate Remote Media Player with Home Assistant.

For more details about this integration, please refer to
https://github.com/shyndman/hass-ffmpeg-player
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import CONF_URL, DOMAIN, LOGGER
from .coordinator import RemoteMediaPlayerCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

# Since this integration is configured through config entries only,
# we use config_entry_only_config_schema
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, _: dict) -> bool:
    """Set up the Remote Media Player component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Remote Media Player from a config entry."""
    try:
        # Initialize coordinator with config entry
        coordinator = RemoteMediaPlayerCoordinator(hass, entry)

        # Set up the coordinator
        await coordinator.async_setup()

        # Store coordinator for use by platforms
        hass.data[DOMAIN][entry.entry_id] = coordinator

        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Register update listener for config changes
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))

        # Register device
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Remote Media Player",
            name=f"Remote Media Player ({entry.data[CONF_URL]})",
            model="Media Player",
            sw_version="0.0.0",
        )
    except Exception as ex:
        LOGGER.error("Failed to set up Remote Media Player: %s", ex)
        raise ConfigEntryNotReady from ex
    else:
        return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Get the coordinator
        coordinator: RemoteMediaPlayerCoordinator = hass.data[DOMAIN][entry.entry_id]

        # Close the WebSocket connection
        await coordinator.client.disconnect()

        # Remove config entry from domain data
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
