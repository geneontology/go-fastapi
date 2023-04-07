import logging
from enum import Enum
from os import path

import yaml

CONFIG = path.join(path.dirname(path.abspath(__file__)), "../conf/config.yaml")

golr_config = None
sparql_config = None
route_mapping = None
logger = logging.getLogger(__name__)


def get_sparql_endpoint():
    global sparql_config
    if sparql_config is None:
        with open(CONFIG, "r") as f:
            sparql_config = yaml.load(f, Loader=yaml.FullLoader)
    return sparql_config["sparql_url"]["url"]


def get_user_agent():
    name = "go-fastapi"
    version = "0.1.1"
    user_agent_array = ["{}/{}".format(name, version)]
    return " ".join(user_agent_array)


def get_golr_config():
    global golr_config
    if golr_config is None:
        with open(CONFIG, "r") as f:
            golr_config = yaml.load(f, Loader=yaml.FullLoader)
    return golr_config


class ESOLR(Enum):
    GOLR = get_golr_config()["solr_url"]["url"]


class ESPARQL(Enum):
    SPARQL = get_sparql_endpoint()


class ESOLRDoc(Enum):
    ONTOLOGY = "ontology_class"
    ANNOTATION = "annotation"
    BIOENTITY = "bioentity"