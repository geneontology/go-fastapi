"""settings for the application."""

import json
import logging
from enum import Enum
from os import path
from urllib.parse import urlparse

import requests
import yaml

CONFIG = path.join(path.dirname(path.abspath(__file__)), "../conf/config.yaml")

golr_config = None
route_mapping = None
index_file_overrides = {}
index_file_cache: dict = {}
logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()


def set_index_file_override(file_key: str, file_path: str):
    """
    Override the path for a specific index file (useful for testing).

    :param file_key: The configuration key (e.g., 'gocam_taxon_index_file')
    :param file_path: The path to the override file
    """
    global index_file_overrides
    index_file_overrides[file_key] = file_path


def clear_index_file_overrides():
    """Clear all index file overrides and any cached index file contents."""
    global index_file_overrides
    index_file_overrides = {}
    index_file_cache.clear()


def _load_index_file(file_key: str, config: dict) -> dict:
    """
    Load a single index file's parsed JSON content, caching it after first load.

    A test override (see :func:`set_index_file_override`) always takes precedence and
    is intentionally never cached, so tests can swap fixture files freely. Otherwise
    the file is fetched once -- from its configured URL (http/https) or a local path --
    and the parsed content is held in :data:`index_file_cache` for the lifetime of the
    process. A given index file is therefore downloaded and parsed at most once;
    restart the service to pick up regenerated index files.

    :param file_key: The configuration key (e.g., 'gocam_entity_index_file').
    :param config: The parsed config.yaml mapping.
    :return: The parsed JSON content of the index file.
    :raises ValueError: If file_key is absent from both overrides and config.
    """
    # Test overrides always win and are intentionally not cached.
    if file_key in index_file_overrides:
        with open(index_file_overrides[file_key], "r") as f:
            return json.load(f)

    if file_key in index_file_cache:
        return index_file_cache[file_key]

    if file_key not in config:
        raise ValueError(f"Configuration key '{file_key}' not found in config.yaml")

    file_config = config[file_key]
    file_url = file_config["url"]
    timeout = file_config.get("timeout", 30)

    parsed = urlparse(file_url)
    if parsed.scheme in ("http", "https"):
        response = requests.get(file_url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    else:
        with open(file_url, "r") as f:
            data = json.load(f)

    index_file_cache[file_key] = data
    return data


def get_index_files(file_key: str = None) -> dict:
    """
    Retrieve JSON index file(s) from either a URL or local path.

    Automatically detects whether the configured path is a URL (http/https) or local
    file path. For URLs, download the file using the configured timeout; for local
    paths, read it from disk. Each index file is loaded at most once per process and
    then served from an in-memory cache, so restart the service to pick up regenerated
    index files (see :func:`_load_index_file`).

    :param file_key: The configuration key (e.g., 'gocam_contributor_index_file').
                     If None, retrieve all index files matching '*_index_file' pattern.
    :return: If file_key is provided, returns the parsed JSON content.
             If file_key is None, returns a dict mapping config keys to their JSON content.
    """
    with open(CONFIG, "r") as f:
        config = yaml.safe_load(f)

    if file_key is None:
        return {k: _load_index_file(k, config) for k in config if k.endswith("_index_file")}

    return _load_index_file(file_key, config)

def get_user_agent():
    """Returns the user agent string."""
    name = "go-fastapi"
    version = "0.1.1"
    user_agent_array = ["{}/{}".format(name, version)]
    return " ".join(user_agent_array)


def get_golr_config():
    """Returns the GOLR configuration."""
    global golr_config
    if golr_config is None:
        with open(CONFIG, "r") as f:
            golr_config = yaml.safe_load(f)
    return golr_config


class ESOLR(Enum):

    """Enum for the GOLR URL."""

    GOLR = get_golr_config()["solr_url"]["url"]


class ESOLRDoc(Enum):

    """Enum for the GOLR document type."""

    ONTOLOGY = "ontology_class"
    ANNOTATION = "annotation"
    BIOENTITY = "bioentity"
