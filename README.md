# Remote Media Player

A Home Assistant integration that provides control of a remote media player via JSON-RPC. This integration acts as a client to control media playback on a remote server.

## Features

- Control remote media playback through Home Assistant
- Real-time state updates via WebSocket
- Support for media metadata (title, artist, album)
- Thumbnail support
- Volume and position control

## Installation

1. Install this integration through HACS, or copy the `remote_media_player` directory to your Home Assistant's `custom_components` directory.
2. Restart Home Assistant
3. Add the integration through the Home Assistant UI

## Configuration

Add to your `configuration.yaml`:

```yaml
media_player:
  - platform: remote_media_player
    host: "localhost"  # The host running your remote media player server
    port: 9300        # The port your server is listening on (default: 9300)
    name: "Remote Player"  # Optional: custom name for the media player
```

## API Documentation

See [API.md](API.md) for the complete JSON-RPC API specification that the remote server should implement.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
