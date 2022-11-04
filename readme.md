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

### Building the image
Simple. `docker build -t putio-helper .` in the /src folder.

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
putio-helper
```

### Example Docker Compose YAML
```yaml
version: '3'

services:
#---------------------------------------------------------------------#
#                Sonarr PutIO Helper -  Send torrents to PutIO        #
#---------------------------------------------------------------------#
  sonarr-putio-helper:
    container_name: sonarr-putio-helper
    image: ghcr.io/dutchminator/putio-helper:latest
    restart: always
    volumes:
      - /path/to/torrent_blackhole:/torrent_blackhole  # or your own mount path
    environment:
      - PUID=  # user id
      - PGID=  # usergroup id
      - TZ=Europe/Amsterdam  # or your own timezone
      - TORRENT_PATH=/torrent_blackhole  # path to mounted torrent blackhole
      - PUTIO_PATH=  # putio path to store transfers
      - TORRENT_POLL_DELAY=1  # poll wait time in seconds
      - PUTIO_OAUTH_TOKEN=  # your OAuth token for putio
```

## Development
### Development TODOs
* [x] Implement PUID/PGID support for Synology usage (and generally, we shouldn't run containers as root :P)
* [x] Implement as Docker container instead of standalone script
* [x] Implement deployment to ghcr.io image registry
* [] Implement CI/CD deployment to an image registry
* [] Implement logging to its own docker folder?
* [] Implement cleanup of torrent_blackhole
* [] Implement cleanup of Putio folder

### How to contribute
TODO