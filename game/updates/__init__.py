import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from itertools import chain
from pathlib import Path

import requests
from packaging.version import parse as vp
from requests import Timeout, ConnectionError

from game.config import UPDATE_URL, UPDATE_FETCHING_TYPE_VERSION, VERSION, APP_DOWNLOAD_URL
from game.utils import rel_to_root, rel_to_writable, temp_path

__all__ = ["APP_UPDATE_AVAILABLE", "DATA_UPDATABLE", "LATEST_APP_VERSION", "UPDATES_CHECKED", "UPDATE_CHECK_SUCCESSFUL",
           "start_update_check", "check_update"]

APP_UPDATE_AVAILABLE = False
APP_REINSTALL_NEEDED = False
DATA_UPDATABLE = []  # [(name-for-download, filepath), ...]
LATEST_APP_VERSION = None
LATEST_INSTALLER_NAME = None

DO_APP_UPDATE = False
STARTED_APP_UPDATE = False
APP_UPDATE_DONE = False

UPDATES_CHECKED = False
IS_UPDATE_CHECKING = False
UPDATE_CHECK_SUCCESSFUL = None

FETCHED_DATASETS = {}

APP_DOWNLOAD_EXECUTOR = None
APP_DOWNLOAD_FUTURE = None


def _fetch_updates():
    """
    Should be called in another thread
    :return: bool (is_successful), string (message)
    """
    global APP_UPDATE_AVAILABLE
    global APP_REINSTALL_NEEDED
    global DATA_UPDATABLE
    global LATEST_APP_VERSION
    global LATEST_INSTALLER_NAME
    global FETCHED_DATASETS
    global IS_UPDATE_CHECKING
    # TODO: Fix blocked quit attempts while running threads
    try:
        # import time
        # time.sleep(3)
        response = requests.get(UPDATE_URL)

        if not 200 <= response.status_code < 300:
            return False, "Server unreachable or not ready"

        data = response.json()

        current_fetching_version = vp(UPDATE_FETCHING_TYPE_VERSION)
        server_fetching_version = vp(data.get("fetching_type_version", "0.0"))

        # Compare Fetching versions
        if current_fetching_version != server_fetching_version:
            if current_fetching_version > server_fetching_version:
                return False, "Server for updates deprecated"
            elif current_fetching_version < server_fetching_version:
                return False, "Application's Update Mechanisms deprecated.\nProbably an update is already available"
            else:
                return False, "Something went wrong while comparing update fetching method versions"

        # f for fetched
        # App version
        app_v = vp(VERSION)
        f_app_v = vp(data["app"])
        if app_v < f_app_v:
            APP_UPDATE_AVAILABLE = True
            LATEST_APP_VERSION = str(f_app_v)
            LATEST_INSTALLER_NAME = data["latest_installer_name"]
            reinstall_v = vp(data["reinstall_needed"])

            if app_v <= reinstall_v:
                APP_REINSTALL_NEEDED = True

        # datasets
        f_datasets = data["datasets"]
        FETCHED_DATASETS = f_datasets
        f_dataset_names = f_datasets.keys()

        for file in chain(Path(rel_to_root("data/")).iterdir(), Path(rel_to_writable("data/")).iterdir()):

            if file.suffix != ".json":
                continue

            name = file.stem

            if name in f_dataset_names:
                with open(file) as d:
                    dataset = json.load(d)

                    data_version = vp(dataset["version"])
                    f_data_version = vp(f_datasets[name]["version"])

                    if data_version < f_data_version:
                        DATA_UPDATABLE.append((file.name, file))

        # print(f"Updatable: {DATA_UPDATABLE}")
        return True, ""

    except (Timeout, ConnectionError) as e:
        print(e)
        return False, "Connection to server timed out or a connection error occurred"

    except (KeyError, ValueError) as e:
        print(e)
        return False, "Couldn't read update data"

    finally:
        IS_UPDATE_CHECKING = False


def start_update_check():
    global IS_UPDATE_CHECKING
    IS_UPDATE_CHECKING = True
    executor = ThreadPoolExecutor()
    thread = executor.submit(_fetch_updates)
    return executor, thread


def check_update(thread: Future, executor: ThreadPoolExecutor):
    global UPDATES_CHECKED
    global UPDATE_CHECK_SUCCESSFUL
    global IS_UPDATE_CHECKING
    global STARTED_APP_UPDATE
    global DO_APP_UPDATE
    global APP_UPDATE_DONE
    global APP_DOWNLOAD_EXECUTOR
    global APP_DOWNLOAD_FUTURE

    if not UPDATES_CHECKED and not IS_UPDATE_CHECKING:
        for task in as_completed([thread]):
            UPDATE_CHECK_SUCCESSFUL, msg = task.result()
            if not UPDATE_CHECK_SUCCESSFUL:
                print(msg)
            break

        executor.shutdown(wait=True)
        UPDATES_CHECKED = True
        IS_UPDATE_CHECKING = False

    if DO_APP_UPDATE and not STARTED_APP_UPDATE:
        DO_APP_UPDATE = False
        STARTED_APP_UPDATE = True
        APP_DOWNLOAD_EXECUTOR = ThreadPoolExecutor()
        APP_DOWNLOAD_FUTURE = APP_DOWNLOAD_EXECUTOR.submit(update_app)
    if STARTED_APP_UPDATE and APP_UPDATE_DONE:
        STARTED_APP_UPDATE = False
        APP_UPDATE_DONE = False
        success, msg = APP_DOWNLOAD_FUTURE.result()
        if success:
            subprocess.Popen([msg], close_fds=True, shell=True)
            if APP_REINSTALL_NEEDED:
                subprocess.Popen([rel_to_root("uninstall.exe")], close_fds=True, shell=True)
            sys.exit()
        else:
            print(msg)


def update_app():
    global APP_UPDATE_DONE
    path = temp_path.joinpath(LATEST_INSTALLER_NAME)
    url = APP_DOWNLOAD_URL + LATEST_INSTALLER_NAME
    with ThreadPoolExecutor() as executor:
        f = executor.submit(download_to_dir, url, path)
        successful, msg = f.result()
    APP_UPDATE_DONE = True
    if not successful:
        return successful, msg

    return True, path


def download_to_dir(url, path):
    # import time
    # time.sleep(3)
    try:
        response = requests.get(url, allow_redirects=True)
        if not 200 <= response.status_code < 300:
            return False, "Server unreachable or not ready"
        with open(path, "wb+") as file:
            file.write(response.content)
        return True, ""

    except (Timeout, ConnectionError) as e:
        print(e)
        return False, "Connection to server timed out or a connection error occurred"
    except PermissionError as e:
        print(e)
        return False, "Permission Error, try running app as Administrator/root"


# def update_datasets():
#     """
#     Should be called in new thread
#     :return: bool, Successful or not
#     """
#
#     def _download_dataset(d):
#         name, path = d
#
#         return True
#
#     with ThreadPoolExecutor() as executor:
#         results = executor.map(_download_dataset, DATA_UPDATABLE)
#
#         for result in results:
#             pass
