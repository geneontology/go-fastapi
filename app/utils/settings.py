"""settings for the application."""

import logging
from enum import Enum
from os import path

import yaml

CONFIG = path.join(path.dirname(path.abspath(__file__)), "../conf/config.yaml")

golr_config = None
sparql_config = None
route_mapping = None
logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()


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
