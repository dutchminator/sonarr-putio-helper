"""
Sonarr Putio Helper

Small application that:
* Monitors a certain directory (= watchfolder) for new torrent/magnet files
* Uploads newly added torrent/magnet files to put.io for download
* Future: Automatically removes files from the watchfolderor putio when they go beyond an age threshold

We will require 4 env variables:
* The folder to watch for torrent/magnet files
* The authentication token for putio
* The directory where putio should store the completed transfer
* The age threshold before we remove files from the watchfolder
"""
# imports
import time
import os
from pathlib import Path

import putiopy
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# Magic constant, check every second unless defined otherwise
TORRENT_POLL_DELAY = 1


def collect_environment() -> tuple[dict | None, Exception | None]:
    """
    Checks whether following env vars are present:
    * PUTIO_OAUTH_TOKEN : Authentication token for putio
    * TORRENT_PATH : Path to watch for file changes
    * PUTIO_PATH : Putio path to store files in for completed transfers
    * TORRENT_POLL_DELAY : optional, time in seconds between polls for file changes. default=1.

    Returns tuple (config, err):
    * config is a dict containing the configuration parameters.
        token: OAuth token
        torrent_path: Path to torrent directory to watch
        putio_path: Path to putio directory
        poll_delay: Time in seconds between torrent directory polls
    * err is None on success, or an Exception on failure
    """
    # TODO Placeholder, implement me!
    try:
        config = {
            "token": os.environ["PUTIO_OAUTH_TOKEN"],
            "torrent_path": os.environ["TORRENT_PATH"],
            "putio_path": os.environ["PUTIO_PATH"],
            "poll_delay": int(os.getenv("TORRENT_POLL_DELAY", TORRENT_POLL_DELAY)),
        }
        return config, None
    except Exception as e:
        return None, Exception(f"environment variable {e} is missing.")


def verify_filesystem(config: dict) -> None | ValueError:
    """
    Check whether the provided paths are valid, exist, and we have permission to read.
    This check verifies that volume mounts are properly set up.

    Returns None on success, or an Exception on failure
    """
    # Check existence of torrent folder in local fs
    try:
        local_path = Path(config["torrent_path"])
        # Check 1. It is indeed a path
        if not local_path.exists():
            raise ValueError("Local torrent path does not exist in container")
        if not local_path.is_dir():
            raise ValueError("Local torrent path is not a valid path for a directory")
        # TODO: Check for proper permissions
        return None

    except Exception as e:
        return e


def connect_putio(config: dict) -> tuple[putiopy.Client | None, Exception | None]:
    """
    Uses the provided putio OAuth token to setup the putio client for use.
    Register an application on your putio account to get your own OAuth token.

    Returns a tuple (client, err):
    * client is the putio client configured using the OAuth token
    * err is None on success, or an Exception on failure
    """

    try:
        client = putiopy.Client(config["token"], use_retry=True)
        response = client.Account.info()
    except putiopy.ClientError as client_err:
        print("PutIO client error: ", client_err.message)
        return None, client_err

    if response["status"] == "OK":
        print(f"PutIO Client: Authenticated as {response['info']['username']}")
        return client, None

    else:
        response_err = Exception(f"PutIO response error: {response}")
        return None, response_err


def configure_torrent_observer(
    config: dict, putio_client: putiopy.Client
) -> tuple[Observer | None, Exception | None]:
    """
    Configures the watchdog observer and event handler actions, and returns the observer.

    Returns a tuple (observer, err):
    * observer is the watchdog observer with defined event handler actions
    * err is None on success, or an Exception on failure
    """
    # Define the event handler object
    torrent_patterns = ["*.magnet", "*.torrent"]  # torrent or magnet files

    torrent_event_handler = PatternMatchingEventHandler(
        patterns=torrent_patterns,
        ignore_patterns=None,
        ignore_directories=True,
        case_sensitive=True,
    )

    # ON: file creation
    def on_torrent_created(event):
        "What to do on file creation event"
        print(f"Observed creation event: {event}")

    torrent_event_handler.on_created = on_torrent_created

    # Define the observer object
    obs_path = config["torrent_path"]
    torrent_observer = Observer()
    torrent_observer.schedule(
        event_handler=torrent_event_handler, path=obs_path, recursive=False
    )

    return torrent_observer, None


if __name__ == "__main__":
    print("Sonarr PutIO Helper: initiating")

    # 1. Check for required environment variables
    config, env_err = collect_environment()
    if env_err:
        raise env_err

    # 2. Check existence of required filesystem directories
    fs_err = verify_filesystem(config)
    if fs_err:
        raise fs_err

    # 3. Verify validity and configure a putio client
    putio_client, putio_err = connect_putio(config)
    if putio_err:
        raise putio_err

    # 4. Verify existence of remote directory
    # TODO

    # 5. Configure the torrent observer
    torrent_observer, obs_err = configure_torrent_observer(config, putio_client)
    if obs_err:
        raise obs_err

    # FUTURE: Configure observers for archival/removal functions

    # 6. Initialize observer loop
    print(f"Starting observer loop with delay {config['poll_delay']}")
    torrent_observer.start()
    try:
        while True:
            time.sleep(config["poll_delay"])
    except KeyboardInterrupt:
        torrent_observer.stop()
        torrent_observer.join()
        print("Sonarr PutIO Helper: Stopped by user.")
