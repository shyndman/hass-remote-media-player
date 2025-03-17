#!/usr/bin/env python3
"""Dummy WebSocket server for testing the Remote Media Player integration."""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

import websockets
from websockets.asyncio.server import ServerConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dummy_server")


class DummyMediaPlayer:
    """Simulates a media player with basic state."""

    def __init__(self) -> None:
        """Initialize the dummy player."""
        self.state = "idle"
        self.position = 0.0
        self.duration = 300.0  # 5 minutes
        self.volume = 0.5
        self.media_url = None
        self.media_type = None
        self.title = "Test Media"
        self.artist = "Test Artist"
        self.album = "Test Album"
        self.last_update = datetime.now(tz=UTC)

    def get_state(self) -> dict[str, Any]:
        """Get the current state."""
        now = datetime.now(tz=UTC)
        if self.state == "playing":
            # Update position based on elapsed time
            elapsed = (now - self.last_update).total_seconds()
            self.position = min(self.position + elapsed, self.duration)

        self.last_update = now

        return {
            "state": self.state,
            "media": {
                "url": self.media_url,
                "media_type": self.media_type,
                "position": self.position,
                "duration": self.duration,
                "title": self.title,
                "artist": self.artist,
                "album": self.album,
                "thumbnail": "http://example.com/thumb.jpg",
            },
            "volume": self.volume,
        }


async def handle_client(websocket: ServerConnection) -> None:
    """Handle a client connection."""
    player = DummyMediaPlayer()
    logger.info("Client connected")

    try:
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if "method" not in data or "id" not in data:
                    continue

                method = data["method"]
                params = data.get("params", {})

                if method == "getState":
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "result": player.get_state(),
                                "id": data["id"],
                            }
                        )
                    )

                elif method == "getSupportedMediaTypes":
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "result": ["video", "music", "url"],
                                "id": data["id"],
                            }
                        )
                    )

                elif method == "play":
                    player.state = "playing"
                    await websocket.send(
                        json.dumps({"jsonrpc": "2.0", "result": True, "id": data["id"]})
                    )
                    # Send state update
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "method": "stateChanged",
                                "params": player.get_state(),
                            }
                        )
                    )

                elif method == "pause":
                    player.state = "paused"
                    await websocket.send(
                        json.dumps({"jsonrpc": "2.0", "result": True, "id": data["id"]})
                    )
                    # Send state update
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "method": "stateChanged",
                                "params": player.get_state(),
                            }
                        )
                    )

                elif method == "stop":
                    player.state = "idle"
                    player.position = 0
                    await websocket.send(
                        json.dumps({"jsonrpc": "2.0", "result": True, "id": data["id"]})
                    )
                    # Send state update
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "method": "stateChanged",
                                "params": player.get_state(),
                            }
                        )
                    )

                elif method == "setVolume":
                    player.volume = params["level"]
                    await websocket.send(
                        json.dumps({"jsonrpc": "2.0", "result": True, "id": data["id"]})
                    )
                    # Send state update
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "method": "stateChanged",
                                "params": player.get_state(),
                            }
                        )
                    )

                elif method == "load":
                    player.media_url = params["url"]
                    player.media_type = params.get("options", {}).get(
                        "media_type", "url"
                    )
                    player.position = params.get("options", {}).get("startPosition", 0)
                    player.state = (
                        "playing"
                        if params.get("options", {}).get("autoplay", True)
                        else "paused"
                    )
                    await websocket.send(
                        json.dumps({"jsonrpc": "2.0", "result": True, "id": data["id"]})
                    )
                    # Send state update
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "method": "stateChanged",
                                "params": player.get_state(),
                            }
                        )
                    )

                else:
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "error": {
                                    "code": -32601,
                                    "message": f"Method {method} not found",
                                },
                                "id": data["id"],
                            }
                        )
                    )

            except json.JSONDecodeError:
                logger.exception("Invalid JSON received")
                continue

    except websockets.ConnectionClosed:
        logger.info("Client disconnected")


async def main() -> None:
    """Run the server."""
    async with websockets.serve(handle_client, "localhost", 9300):
        logger.info("Server started on ws://localhost:9300")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
