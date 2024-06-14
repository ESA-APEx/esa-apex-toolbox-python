from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Optional, Union

import requests


def _load_json_resource(src: Union[dict, str, Path]) -> dict:
    """Load a JSON resource from a file or a string."""
    if isinstance(src, dict):
        return src
    elif isinstance(src, Path):
        with open(src, "r", encoding="utf8") as f:
            return json.load(f)
    elif isinstance(src, str):
        if src.strip().startswith("{"):
            # Assume the string is JSON payload
            return json.loads(src)
        elif src.startswith("http://") or src.startswith("https://"):
            # Assume the string is a URL to a JSON resource
            resp = requests.get(src)
            resp.raise_for_status()
            return resp.json()
        else:
            # Assume the string is a file path
            return _load_json_resource(Path(src))
    else:
        # TODO: support bytes, file-like objects, etc.
        raise ValueError(f"Unsupported JSON resource type {type(src)}")


@dataclasses.dataclass(frozen=True)
class Algorithm:
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    # TODO more fields

    @classmethod
    def from_ogc_api_record(cls, src: Union[dict, str, Path]) -> Algorithm:
        """
        Load an algorithm from an 'OGC API - Records' record object, specified
        as a dict, a JSON string, a file path, or a URL.
        """
        data = _load_json_resource(src)

        # TODO dedicated exceptions for structure/schema violations
        if not data.get("type") == "Feature":
            raise ValueError("Expected a GeoJSON Feature object")
        if "http://www.opengis.net/spec/ogcapi-records-1/1.0/req/record-core" not in data.get("conformsTo", []):
            raise ValueError("Expected an OGC API - Records record object")

        properties = data.get("properties", {})
        if not properties.get("type") == "apex_algorithm":
            raise ValueError("Expected an APEX algorithm object")

        return cls(
            id=data["id"],
            title=properties.get("title"),
            description=properties.get("description"),
        )
