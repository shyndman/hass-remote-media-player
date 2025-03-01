"""Media Player platform for ffmpeg_player."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityDescription,
)

from .entity import FFmpegPlayerEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import FFmpegDataUpdateCoordinator
    from .data import FFmpegPlayerConfigEntry

ENTITY_DESCRIPTIONS = (
    MediaPlayerEntityDescription(
        key="ffmpeg_player",
        name="Integration MediaPlayer",
        icon="mdi:format-quote-close",
    ),
)
