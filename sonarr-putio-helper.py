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


def get_or_create_putio_folder(
    config: dict, putio_client: putiopy.Client
) -> tuple[int | None, Exception | None]:
    """
    Folders on Putio are identified via integer (so-called parent_id).
    Unfortunately there is no notion of paths in Putio.
    Instead, a folder has an id and a parent_id identifying its parent. (root id=0).

    Using Putio API /files/list we recursively retrieve the parent_id for a given folder name in the provided path,
    or we create the folder if it does not yet exist using Putio API /files/create-folder.

    Params:
        * config : dict, containing our configuration options
        * putio_client : A properly configured Putio client

    returns:
        A Tuple consisting of
        * int : On success, the integer identifier (=parent_id) for the putio remote folder. On failure, None.
        * Exception : On failure, an Exception object. On success, None.
    """
    # Traverse putio's folder hierarchy to get the relevant parent_id
    putio_path = config["putio_path"]
    putio_folders = putio_path.split("/")
    parent_id = 0  # Start at root of Putio files structure
    created_parent = False  # once we create a parent folder, we skip the File.List calls as they will always be empty.

    for folder in putio_folders:
        # skip empty-string, e.g. for trailing slash or double slash in path
        if folder == "":
            continue

        # If the current parent_id has not been created by us
        if not created_parent:
            # List every folder at current parent_id
            putio_folder_list = putio_client.File.list(
                parent_id=parent_id, file_type="FOLDER"
            )
            print(putio_folder_list)

            # Search for the current "folder" name
            matching_folder = [f for f in putio_folder_list if f.name == folder]
        else:
            # output of client.File.list() on created parents will always be an empty list
            matching_folder = []

        # If it exists (list length >= 1), cool, collect its id as parent_id and move to next folder
        if matching_folder:
            parent_id = matching_folder[0].id
        else:
            # If it does not yet exist, create it in current parent_id
            try:
                new_putio_folder_obj = putio_client.File.create_folder(
                    folder, parent_id=parent_id
                )
                print(
                    f"Created new Putio folder [{folder}] in parent_id [{parent_id}]."
                )
            except Exception as e:
                # We don't expect an issue creating the folder as it didn't exist, but who knows....
                return None, e

            # output of putio_client.File.create_folder() is a putiopy.File object
            parent_id = new_putio_folder_obj.id
            created_parent = True

    # End of for-loop, parent_id should now be the id of the target folder on Putio!
    print(f"Target folder [{putio_path}] on Putio has parent_id {parent_id}")

    # return parent_id value for target putio folder
    return parent_id, None


def configure_torrent_observer(
    config: dict, target_parent_id: int, putio_client: putiopy.Client
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
        """
        What to do on file creation event
        """
        print(f"Observed creation event: {event}")

        # Get the file from the event
        new_torrent = event.src_path
        try:
            putio_transfer = putio_client.Transfer.add_torrent(
                path=new_torrent,
                parent_id=target_parent_id,
            )
        except Exception as e:
            raise e

        print(f"PutIO transfer response: {putio_transfer}")

    # Assign on_created function to event handler
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
    putio_parent_id, putio_folder_err = get_or_create_putio_folder(config, putio_client)
    if putio_folder_err:
        raise putio_folder_err

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
