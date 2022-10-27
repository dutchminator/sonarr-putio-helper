# Sonarr Putio Helper

Scans a local folder for new torrent/magnet files, and starts a transfer on Putio in the designated target folder. It scans for new torrent/magnet files every POLL_DELAY seconds.

## Usage
### Required environment variables
- TORRENT_PATH: /path/to/torrent_folder
- PUTIO_PATH: path/on/putio
- TORRENT_POLL_DELAY: Number of seconds in integer
- PUTIO_OAUTH_TOKEN: OAUTH Token to authenticate to your Putio account
- PUID: ID for the user with permissions to torrent folder
- PGID: ID for the group the user belongs to with permissions to the torrent folder

### Example docker run statement
```bash
docker run -it \
-e TORRENT_PATH=/torrent_blackhole \
-e PUTIO_PATH=sonarr \
-e TORRENT_POLL_DELAY=1 \
-e PUTIO_OAUTH_TOKEN=YOURTOKENGOESHERE \
-e PGID=65541 \
-e PUID=1029 \
-v Path/To/torrent_blackhole_test:/torrent_blackhole \
putio-helper:0.3
```

### Example Docker Compose YAML
TODO

## Development
### Development TODOs
[x] Implement PUID/PGID support for Synology usage (and generally, we shouldn't run containers as root :P)
[x] Implement as Docker container instead of standalone script
[] Implement CI/CD deployment to an image registry
[] Implement logging to its own docker folder?
[] Implement cleanup of torrent_blackhole
[] Implement cleanup of Putio folder

### How to contribute
TODO