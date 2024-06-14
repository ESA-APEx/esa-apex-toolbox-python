from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Optional, Union

import requests


class LINK_REL:
    UDP = "udp"


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


class InvalidMetadataError(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class UdpLink:
    href: str
    title: Optional[str] = None

    @classmethod
    def from_link_object(cls, data: dict) -> UdpLink:
        """Parse a link object (dict/mapping) into a UdpLink object."""
        if "rel" not in data:
            raise InvalidMetadataError("Missing 'rel' attribute in link object")
        if data["rel"] != LINK_REL.UDP:
            raise InvalidMetadataError(f"Expected link with rel='udp' but got {data['rel']!r}")
        if "type" in data and data["type"] != "application/json":
            raise InvalidMetadataError(f"Expected link with type='application/json' but got {data['type']!r}")
        if "href" not in data:
            raise InvalidMetadataError("Missing 'href' attribute in link object")
        return cls(
            href=data["href"],
            title=data.get("title"),
        )


@dataclasses.dataclass(frozen=True)
class Algorithm:
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    udp_link: Optional[UdpLink] = None
    # TODO more fields

    @classmethod
    def from_ogc_api_record(cls, src: Union[dict, str, Path]) -> Algorithm:
        """
        Load an algorithm from an 'OGC API - Records' record object, specified
        as a dict, a JSON string, a file path, or a URL.
        """
        data = _load_json_resource(src)

        if not data.get("type") == "Feature":
            raise InvalidMetadataError(f"Expected a GeoJSON 'Feature' object, but got type {data.get('type')!r}.")
        if "http://www.opengis.net/spec/ogcapi-records-1/1.0/req/record-core" not in data.get("conformsTo", []):
            raise InvalidMetadataError(
                f"Expected an 'OGC API - Records' record object, but got {data.get('conformsTo')!r}."
            )

        properties = data.get("properties", {})
        if properties.get("type") != "apex_algorithm":
            raise InvalidMetadataError(f"Expected an APEX algorithm object, but got type {properties.get('type')!r}.")

        links = data.get("links", [])
        udp_links = [UdpLink.from_link_object(link) for link in links if link.get("rel") == LINK_REL.UDP]
        if len(udp_links) > 1:
            raise InvalidMetadataError("Multiple UDP links found")
        # TODO: is having a UDP link a requirement?
        udp_link = udp_links[0] if udp_links else None

        return cls(
            id=data["id"],
            title=properties.get("title"),
            description=properties.get("description"),
            udp_link=udp_link,
        )
