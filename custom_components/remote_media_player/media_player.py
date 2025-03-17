"""Support for Remote Media Player."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, override

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.const import CONF_NAME
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import RemoteMediaPlayerCoordinator

_LOGGER = logging.getLogger(__name__)

# Features our media player supports
SUPPORT_REMOTE_PLAYER = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.PLAY_MEDIA
)

# Map of server media types to Home Assistant media types
MEDIA_TYPE_MAP = {
    "video": MediaType.VIDEO,
    "music": MediaType.MUSIC,
    "playlist": MediaType.PLAYLIST,
    "tvshow": MediaType.TVSHOW,
    "episode": MediaType.EPISODE,
    "channel": MediaType.CHANNEL,
    "movie": MediaType.MOVIE,
    "podcast": MediaType.PODCAST,
    "url": MediaType.URL,
    "image": MediaType.IMAGE,
    "game": MediaType.GAME,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remote Media Player from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RemoteMediaPlayer(coordinator, entry)])


class RemoteMediaPlayer(MediaPlayerEntity):
    """Representation of a Remote Media Player."""

    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_supported_features = SUPPORT_REMOTE_PLAYER

    def __init__(
        self, coordinator: RemoteMediaPlayerCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the media player."""
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.data[CONF_NAME]
        self.coordinator = coordinator
        self._supported_media_types: list[str] = []

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()
        # Get supported media types from server
        try:
            self._supported_media_types = (
                await self.coordinator.client.get_supported_media_types()
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to get supported media types: %s", err)
            self._supported_media_types = ["url"]  # Fallback to basic URL support

    @property
    @override
    def available(self) -> bool:
        """Return if the media player is available."""
        return self.coordinator.last_update_success

    @property
    @override
    def state(self) -> MediaPlayerState | None:
        """Return the state of the media player."""
        if not self.coordinator.data:
            return None

        state = self.coordinator.data.get("state")
        if state == "playing":
            return MediaPlayerState.PLAYING
        if state == "paused":
            return MediaPlayerState.PAUSED
        if state == "idle":
            return MediaPlayerState.IDLE
        if state == "error":
            return MediaPlayerState.OFF  # Use OFF instead of PROBLEM for error state
        return None

    @property
    @override
    def media_position(self) -> float | None:
        """Return the position of current playing media in seconds."""
        if not self.coordinator.data:
            return None

        media = self.coordinator.data.get("media", {})
        return media.get("position")

    @property
    @override
    def media_duration(self) -> float | None:
        """Return the duration of current playing media in seconds."""
        if not self.coordinator.data:
            return None

        media = self.coordinator.data.get("media", {})
        return media.get("duration")

    @property
    @override
    def media_title(self) -> str | None:
        """Return the title of current playing media."""
        if not self.coordinator.data:
            return None

        media = self.coordinator.data.get("media", {})
        return media.get("title")

    @property
    @override
    def media_artist(self) -> str | None:
        """Return the artist of current playing media."""
        if not self.coordinator.data:
            return None

        media = self.coordinator.data.get("media", {})
        return media.get("artist")

    @property
    @override
    def media_album_name(self) -> str | None:
        """Return the album of current playing media."""
        if not self.coordinator.data:
            return None

        media = self.coordinator.data.get("media", {})
        return media.get("album")

    @property
    @override
    def media_image_url(self) -> str | None:
        """Return the image URL of current playing media."""
        if not self.coordinator.data:
            return None

        media = self.coordinator.data.get("media", {})
        return media.get("thumbnail")

    @property
    @override
    def volume_level(self) -> float | None:
        """Return the volume level."""
        if not self.coordinator.data:
            return None

        return self.coordinator.data.get("volume")

    @property
    def supported_media_types(self) -> list[str]:
        """Return the list of supported media types."""
        return [
            MEDIA_TYPE_MAP[t]
            for t in self._supported_media_types
            if t in MEDIA_TYPE_MAP
        ]

    @override
    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        # Convert HA media type back to server media type
        server_media_type = next(
            (k for k, v in MEDIA_TYPE_MAP.items() if v == media_type),
            "url",  # Default to URL if type not found
        )

        if server_media_type not in self._supported_media_types:
            msg = f"Unsupported media type {media_type}"
            raise HomeAssistantError(msg)

        # Pass media type to server
        await self.coordinator.client.load(
            media_id, {"media_type": server_media_type, **kwargs}
        )

    @override
    async def async_media_play(self) -> None:
        """Send play command."""
        await self.coordinator.client.play()

    @override
    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self.coordinator.client.pause()

    @override
    async def async_media_stop(self) -> None:
        """Send stop command."""
        await self.coordinator.client.stop()

    @override
    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        await self.coordinator.client.set_volume(volume)

    @override
    async def async_media_seek(self, position: float) -> None:
        """Seek the media to a specific location."""
        await self.coordinator.client.seek(position)
