"""API client for Remote Media Player JSON-RPC interface."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import TYPE_CHECKING, Any

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed, WebSocketException

if TYPE_CHECKING:
    from collections.abc import Callable

    from websockets.typing import Data

_LOGGER = logging.getLogger(__name__)


class ApiClientError(Exception):
    """General API client error."""


class ApiClientConnectionError(ApiClientError):
    """API client connection error."""


class RemoteMediaPlayerClient:
    """Remote Media Player JSON-RPC client."""

    def __init__(self, url: str) -> None:
        """Initialize the client."""
        self._url = url
        self._websocket: ClientConnection | None = None
        self._message_id = 0
        self._state_callback: Callable[[dict[str, Any]], None] | None = None
        self._error_callback: Callable[[str], None] | None = None
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._response_futures: dict[int, asyncio.Future[dict[str, Any]]] = {}

    async def connect(self) -> None:
        """Connect to the remote media player."""
        if self._websocket:
            return

        try:
            self._websocket = await connect(
                self._url,
                ping_timeout=30,
                close_timeout=10,
            )
            self._task = asyncio.create_task(self._listen())
        except (ConnectionError, WebSocketException) as err:
            msg = f"Failed to connect: {err}"
            raise ApiClientConnectionError(msg) from err

    async def disconnect(self) -> None:
        """Disconnect from the remote media player."""
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        if self._websocket:
            await self._websocket.close()
            self._websocket = None

        # Clear any pending futures
        for future in self._response_futures.values():
            if not future.done():
                future.cancel()
        self._response_futures.clear()

    def set_state_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Set callback for state updates."""
        self._state_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for errors."""
        self._error_callback = callback

    def _handle_message(self, message: Data) -> None:
        """Handle a message from the WebSocket connection."""
        try:
            if isinstance(message, bytes):
                message = message.decode()

            data = json.loads(message)

            # Handle responses to requests
            if "id" in data:
                msg_id = data["id"]
                if msg_id in self._response_futures:
                    future = self._response_futures.pop(msg_id)
                    if "error" in data:
                        future.set_exception(ApiClientError(data["error"]["message"]))
                    else:
                        future.set_result(data.get("result", {}))
                return

            # Handle notifications
            if "method" in data:
                if data["method"] == "stateChanged" and self._state_callback:
                    self._state_callback(data["params"])
                elif data["method"] == "error" and self._error_callback:
                    self._error_callback(data["params"]["message"])
        except json.JSONDecodeError:
            _LOGGER.exception("Failed to decode message")
        except KeyError:
            _LOGGER.exception("Invalid message format")
        except UnicodeDecodeError:
            _LOGGER.exception("Failed to decode binary message")

    async def _listen(self) -> None:
        """Listen for messages from the server."""
        if not self._websocket:
            return

        try:
            async for message in self._websocket:
                self._handle_message(message)
        except ConnectionClosed:
            if self._error_callback:
                self._error_callback("Connection closed")
        except Exception as err:
            _LOGGER.exception("WebSocket error")
            if self._error_callback:
                self._error_callback(str(err))

    async def _send_command(
        self, method: str, params: dict[str, Any] | None = None
    ) -> Any:
        """Send command to the remote media player."""
        if not self._websocket:
            msg = "Not connected"
            raise ApiClientConnectionError(msg)

        async with self._lock:
            self._message_id += 1
            msg_id = self._message_id
            message = {
                "jsonrpc": "2.0",
                "method": method,
                "id": msg_id,
            }
            if params:
                message["params"] = params

            # Create a future for the response
            future = asyncio.get_running_loop().create_future()
            self._response_futures[msg_id] = future

            try:
                await self._websocket.send(json.dumps(message))
                return await asyncio.wait_for(future, timeout=10.0)
            except TimeoutError as err:
                self._response_futures.pop(msg_id, None)
                msg = f"Command timed out: {method}"
                raise ApiClientConnectionError(msg) from err
            except (ConnectionError, WebSocketException) as err:
                self._response_futures.pop(msg_id, None)
                msg = f"Command failed: {err}"
                raise ApiClientConnectionError(msg) from err

    async def play(self) -> None:
        """Send play command."""
        await self._send_command("play")

    async def pause(self) -> None:
        """Send pause command."""
        await self._send_command("pause")

    async def stop(self) -> None:
        """Send stop command."""
        await self._send_command("stop")

    async def load(self, url: str, options: dict[str, Any] | None = None) -> None:
        """Load media from URL."""
        params: dict[str, Any] = {"url": url}
        if options:
            params["options"] = options
        await self._send_command("load", params)

    async def set_volume(self, level: float) -> None:
        """Set volume level (0.0 to 1.0)."""
        await self._send_command("setVolume", {"level": level})

    async def seek(self, position: float) -> None:
        """Seek to position in seconds."""
        await self._send_command("seek", {"position": position})

    async def get_state(self) -> dict[str, Any]:
        """Get current player state."""
        return await self._send_command("getState")

    async def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types from the server."""
        return await self._send_command("getSupportedMediaTypes")
