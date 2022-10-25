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


def collect_environment():
    """
    Checks whether following env vars are present:
    * PUTIO_OAUTH_TOKEN : Authentication token for putio
    * TORRENT_PATH : Path to watch for file changes
    * PUTIO_PATH : Putio path to store files in for completed transfers

    Returns tuple (config, err):
    * config is a dict containing the token and paths
    * err is None on success, or an Exception on failure
    """
    # TODO Placeholder, implement me!
    try:
        config = {
            "token": os.environ["PUTIO_OAUTH_TOKEN"],
            "watchfolder": os.environ["TORRENT_PATH"],
            "putio_path": os.environ["PUTIO_PATH"],
            "poll_delay": os.getenv("TORRENT_POLL_DELAY", TORRENT_POLL_DELAY),
        }
        return config, None
    except Exception as e:
        return None, Exception(f"environment variable {e} is missing.")


def verify_filesystem(config: dict):
    """
    Check whether the provided paths are valid, exist, and we have permission to read.
    This check verifies that volume mounts are properly set up.

    Returns None on success, or an Exception on failure
    """
    # Check existence of torrent folder in local fs
    try:
        local_path = Path(config["watchfolder"])
        # Check 1. It is indeed a path
        if not local_path.exists():
            raise ValueError("Local torrent path does not exist in container")
        if not local_path.is_dir():
            raise ValueError("Local torrent path is not a valid path for a directory")
        # TODO: Check for proper permissions
        return None

    except Exception as e:
        return e


def connect_putio(config: dict):
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


def configure_observer(config: dict, putio_client: putiopy.Client):
    """
    Configures the watchdog observer and event handler actions, and returns the observer.

    Returns a tuple (observer, err):
    * observer is the watchdog observer with defined event handler actions
    * err is None on success, or an Exception on failure
    """
    # TODO Placeholder
    return None, Exception("Error [C1]: Not yet implemented, TODO!")


if __name__ == "__main__":
    print("Hello world! :)")

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
    torrent_observer, obs_err = configure_observer(config, putio_client)
    if obs_err:
        raise obs_err

    # 6. Initialize observer loop
    torrent_observer.start()
    try:
        while True:
            time.sleep(config["poll_delay"])
    except KeyboardInterrupt:
        torrent_observer.stop()
        torrent_observer.join()

    # 6. FUTURE: Initialize archiver loop for watchfolder files

    # 7. FUTURE: Initialize archiver loop for putio files
