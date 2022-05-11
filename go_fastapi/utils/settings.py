import yaml
from os import path

# This is set to false to prevent Flask-Restplus from
# changing the error message structure
ERROR_INCLUDE_MESSAGE = False

CONFIG = path.join(path.dirname(path.abspath(__file__)), '../conf/config.yaml')
biolink_config = None
route_mapping = None


def get_biolink_config():
    global biolink_config
    if biolink_config is None:
        with open(CONFIG, 'r') as f:
            biolink_config = yaml.load(f, Loader=yaml.FullLoader)
    return biolink_config
