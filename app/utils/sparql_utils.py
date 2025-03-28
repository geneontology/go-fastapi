"""Utils for SPARQL queries."""

from typing import Any

from fastapi.responses import ORJSONResponse


def create_response(data: Any):
    """
    Create a response with the given data.

    :param data:
    :return:
    """
    return ORJSONResponse(content=data.dict())


SEPARATOR = "|"  # separator for splitting values


def transform(data, keys_to_split=None):
    """
    Transform a SPARQL json result.

    by:
    1) outputting only { key : value }, removing datatype
    2) for some keys, transform them into array based on SEPARATOR.
    """
    transformed = {}
    for key in data:
        if key in keys_to_split:
            transformed[key] = data[key]["value"].split(SEPARATOR)
        else:
            transformed[key] = data[key]["value"]
    return transformed


def transform_array(data, keys_to_split=None):
    """Transform a SPARQL json array based on the rules of transform."""
    if keys_to_split is None:
        keys_to_split = []
    transformed = []
    for item in data:
        transformed.append(transform(item, keys_to_split))
    return transformed
