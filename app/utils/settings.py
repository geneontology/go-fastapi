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
sparql_config = None
route_mapping = None
logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()


def get_index_files(file_key: str = None) -> dict:
    """Retrieve JSON index file(s) from either a URL or local path.

    Automatically detects whether the configured path is a URL (http/https) or local file path.
    For URLs, download the file using the configured timeout.
    For local paths, read the file directly from disk.

    :param file_key: The configuration key (e.g., 'gocam_contributor_index_file').
                     If None, retrieve all index files matching '*_index_file' pattern.
    :return: If file_key is provided, returns the parsed JSON content.
             If file_key is None, returns a dict mapping config keys to their JSON content.
    """
    with open(CONFIG, "r") as f:
        config = yaml.safe_load(f)

    if file_key is None:
        index_files = {k: v for k, v in config.items() if k.endswith("_index_file")}
        result = {}
        for key, file_config in index_files.items():
            file_url = file_config["url"]
            timeout = file_config.get("timeout", 30)

            parsed = urlparse(file_url)
            if parsed.scheme in ("http", "https"):
                response = requests.get(file_url, timeout=timeout)
                response.raise_for_status()
                result[key] = response.json()
            else:
                with open(file_url, "r") as f:
                    result[key] = json.load(f)
        return result

    if file_key not in config:
        raise ValueError(f"Configuration key '{file_key}' not found in config.yaml")

    file_config = config[file_key]
    file_url = file_config["url"]
    timeout = file_config.get("timeout", 30)

    parsed = urlparse(file_url)
    if parsed.scheme in ("http", "https"):
        response = requests.get(file_url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    else:
        with open(file_url, "r") as f:
            return json.load(f)


def get_sparql_endpoint():
    """Returns the SPARQL endpoint URL."""
    global sparql_config
    if sparql_config is None:
        with open(CONFIG, "r") as f:
            sparql_config = yaml.safe_load(f)
    return sparql_config["sparql_url"]["url"]


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


class ESPARQL(Enum):

    """Enum for the SPARQL endpoint URL."""

    SPARQL = get_sparql_endpoint()


class ESOLRDoc(Enum):

    """Enum for the GOLR document type."""

    ONTOLOGY = "ontology_class"
    ANNOTATION = "annotation"
    BIOENTITY = "bioentity"
