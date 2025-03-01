"""Custom types for ffmpeg_player."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import FFmpegPlayerApiClient
    from .coordinator import FFmpegDataUpdateCoordinator


type FFmpegPlayerConfigEntry = ConfigEntry[FFmpegPlayerData]


@dataclass
class FFmpegPlayerData:
    """Data for the Blueprint integration."""

    client: FFmpegPlayerApiClient
    coordinator: FFmpegDataUpdateCoordinator
    integration: Integration
