# JSON-RPC Media Player API Specification

This document defines the JSON-RPC 2.0 API for communication between the Home Assistant media player integration and the remote media player server.

## Transport

- Protocol: JSON-RPC 2.0
- Transport: WebSocket
- Default Port: 9300 (configurable)
- Endpoint: `ws://<host>:<port>/ws`

## Methods

### Player Control Methods

#### play()
Starts or resumes playback.
```json
-> {"jsonrpc": "2.0", "method": "play", "id": 1}
<- {"jsonrpc": "2.0", "result": true, "id": 1}
```

#### pause()
Pauses playback.
```json
-> {"jsonrpc": "2.0", "method": "pause", "id": 1}
<- {"jsonrpc": "2.0", "result": true, "id": 1}
```

#### stop()
Stops playback and unloads the current media.
```json
-> {"jsonrpc": "2.0", "method": "stop", "id": 1}
<- {"jsonrpc": "2.0", "result": true, "id": 1}
```

#### load(url, [options])
Loads media from the specified URL.
```json
-> {
    "jsonrpc": "2.0",
    "method": "load",
    "params": {
        "url": "http://example.com/media.mp4",
        "options": {
            "media_type": "video",
            "startPosition": 0,
            "autoplay": true
        }
    },
    "id": 1
}
<- {"jsonrpc": "2.0", "result": true, "id": 1}
```

#### setVolume(level)
Sets the volume level (0.0 to 1.0).
```json
-> {
    "jsonrpc": "2.0",
    "method": "setVolume",
    "params": {
        "level": 0.5
    },
    "id": 1
}
<- {"jsonrpc": "2.0", "result": true, "id": 1}
```

#### seek(position)
Seeks to the specified position in seconds.
```json
-> {
    "jsonrpc": "2.0",
    "method": "seek",
    "params": {
        "position": 120.5
    },
    "id": 1
}
<- {"jsonrpc": "2.0", "result": true, "id": 1}
```

### Query Methods

#### getState()
Returns the current player state.
```json
-> {"jsonrpc": "2.0", "method": "getState", "id": 1}
<- {
    "jsonrpc": "2.0",
    "result": {
        "state": "playing",  // playing, paused, idle, error
        "media": {
            "url": "http://example.com/media.mp4",
            "media_type": "video",
            "duration": 360.5,
            "position": 65.4,
            "title": "Sample Media",  // optional
            "artist": "Unknown",      // optional
            "album": "Unknown",       // optional
            "thumbnail": "http://example.com/thumb.jpg"  // optional
        },
        "volume": 0.5,
        "muted": false,
        "error": null  // string if state is "error"
    },
    "id": 1
}
```

#### getSupportedMediaTypes()
Returns a list of media types supported by the player.
```json
-> {"jsonrpc": "2.0", "method": "getSupportedMediaTypes", "id": 1}
<- {
    "jsonrpc": "2.0",
    "result": [
        "video",
        "music",
        "playlist",
        "tvshow",
        "episode",
        "channel",
        "movie",
        "podcast",
        "url",
        "image",
        "game"
    ],
    "id": 1
}
```

## Notifications

The server sends state updates to the client using notifications (messages without an id).

### stateChanged
Sent when any player state changes.
```json
<- {
    "jsonrpc": "2.0",
    "method": "stateChanged",
    "params": {
        // Same structure as getState() result
    }
}
```

### error
Sent when an error occurs.
```json
<- {
    "jsonrpc": "2.0",
    "method": "error",
    "params": {
        "code": 500,
        "message": "Failed to load media"
    }
}
```

## Error Codes

Standard JSON-RPC error codes:
- -32700: Parse error
- -32600: Invalid request
- -32601: Method not found
- -32602: Invalid params
- -32603: Internal error

Application-specific error codes:
- -32000: Media load failed
- -32001: Invalid media URL
- -32002: Network error
- -32003: Player error
- -32004: Unsupported media type

## Media Types

The following media types are supported:
- `video`: Video files and streams
- `music`: Music files and audio streams
- `playlist`: Media playlists
- `tvshow`: TV shows
- `episode`: TV show episodes
- `channel`: Live channels or streams
- `movie`: Movies
- `podcast`: Podcast episodes
- `url`: Generic URLs
- `image`: Images
- `game`: Game content

## State Machine

The player can be in one of these states:
- `idle`: No media loaded
- `playing`: Media is playing
- `paused`: Media is paused
- `error`: An error has occurred

State transitions:
1. `idle` → `playing`: After successful `load()` with autoplay or `play()`
2. `playing` → `paused`: After `pause()`
3. `paused` → `playing`: After `play()`
4. Any state → `idle`: After `stop()`
5. Any state → `error`: After an error occurs
6. `error` → `idle`: After `stop()`

## Implementation Notes

1. All methods should return errors if the operation cannot be completed
2. The server should maintain the last known state and send it upon new client connections
3. Volume changes should persist across media loads
4. Media position should be reported with at least 0.1 second precision
5. The server should validate all URLs before attempting to load them
6. Thumbnail URLs, if provided, should be directly loadable by Home Assistant
7. The server should validate media types against its supported types list
8. If a media type is not specified in `load()`, the server should attempt to detect it
9. The server should maintain a consistent mapping between its media types and Home Assistant media types
