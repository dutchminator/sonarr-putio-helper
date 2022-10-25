# Sonarr Putio Helper

Scans a local folder for new torrent/magnet files, and starts a transfer on Putio in the designated target folder. It scans for new torrent/magnet files every POLL_DELAY seconds.

## Required environment variables
- TORRENT_PATH: /path/to/torrent_folder
- PUTIO_PATH: path/on/putio
- TORRENT_POLL_DELAY: Number of seconds in integer
- PUTIO_OAUTH_TOKEN: OAUTH Token to authenticate to your Putio account

## Development TODOs
- Implement as Docker container instead of standalone script
- Implement logging to its own docker folder?
- Implement cleanup of torrent_blackhole
- Implement cleanup of Putio folder