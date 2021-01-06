"""
Import using import game.datasets instead of from ... import ...
to ensure that all variables are synced
"""
import json
from itertools import zip_longest
from pathlib import Path

from game.utils import rel_to_root, rel_to_writable

__all__ = ["DATASET_PATH_LIST", "load_datasets", "DATASET_INFO"]

DATASET_PATH_LIST = []
DATASET_INFO = []


def load_datasets() -> list:
    """
    Collects all datasets and returns a list of paths to them.
    Call in thread
    :return: list of all paths to the datasets
    """
    datasets = []
    infos = []
    global DATASET_PATH_LIST
    global DATASET_INFO

    for b, custom in zip_longest(Path(rel_to_root("data/")).iterdir(), Path(rel_to_writable("data/")).iterdir()):
        if b is not None and b.suffix == ".json":
            datasets.append(b)
        if custom is not None and custom.suffix == ".json":
            datasets.append(custom)

    for path in datasets:
        with open(path, encoding="utf-8") as file:
            dataset = json.load(file)
            info = {
                "name": dataset.get("name", path.stem),
                "version": dataset.get("version", "unknown"),
                "description": dataset.get("description", "-"),
                "lang": dataset.get("lang", "unknown"),
                "categories": dataset.get("categories", "unknown"),
                "image_path": dataset.get("image_path", "undefinedimage.png"),
                "filename": path.name,
                "path": path
            }
            infos.append(info)
    DATASET_INFO = infos
    DATASET_PATH_LIST = datasets
    return datasets
