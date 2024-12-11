import re
from pathlib import Path

import pytest

from esa_apex_toolbox.algorithms import (
    Algorithm,
    GithubAlgorithmRepository,
    InvalidMetadataError,
    UdpLink,
)

DATA_ROOT = Path(__file__).parent / "data"


class TestUdpLink:
    def test_from_link_object_basic(self):
        data = {
            "rel": "openeo-process",
            "href": "https://esa-apex.test/udp/basic.json",
        }
        link = UdpLink.from_link_object(data)
        assert link.href == "https://esa-apex.test/udp/basic.json"
        assert link.title is None

    def test_from_link_object_with_title(self):
        data = {
            "rel": "openeo-process",
            "href": "https://esa-apex.test/udp/basic.json",
            "title": "My basic UDP",
        }
        link = UdpLink.from_link_object(data)
        assert link.href == "https://esa-apex.test/udp/basic.json"
        assert link.title == "My basic UDP"

    def test_from_link_object_missing_rel(self):
        data = {
            "href": "https://esa-apex.test/udp/basic.json",
        }
        with pytest.raises(InvalidMetadataError, match="Missing 'rel' attribute"):
            _ = UdpLink.from_link_object(data)

    def test_from_link_object_wrong_rel(self):
        data = {
            "rel": "self",
            "href": "https://esa-apex.test/udp/basic.json",
        }
        with pytest.raises(InvalidMetadataError, match="Expected link with rel='udp'"):
            _ = UdpLink.from_link_object(data)

    def test_from_link_object_no_href(self):
        data = {
            "rel": "openeo-process",
        }
        with pytest.raises(InvalidMetadataError, match="Missing 'href' attribute"):
            _ = UdpLink.from_link_object(data)

    def test_from_link_object_wrong_type(self):
        data = {
            "rel": "openeo-process",
            "href": "https://esa-apex.test/udp/basic.json",
            "type": "application/xml",
        }
        with pytest.raises(InvalidMetadataError, match="Expected link with type='application/json'"):
            _ = UdpLink.from_link_object(data)


class TestAlgorithm:
    def test_from_ogc_api_record_minimal(self):
        data = {
            "id": "minimal",
            "type": "Feature",
            "conformsTo": ["http://www.opengis.net/spec/ogcapi-records-1/1.0/req/record-core"],
            "properties": {
                "type": "apex_algorithm",
            },
        }
        algorithm = Algorithm.from_ogc_api_record(data)
        assert algorithm.id == "minimal"

    def test_from_ogc_api_record_wrong_type(self):
        data = {
            "id": "wrong",
            "type": "apex_algorithm",
            "conformsTo": ["http://www.opengis.net/spec/ogcapi-records-1/1.0/req/record-core"],
        }
        with pytest.raises(
            InvalidMetadataError, match="Expected a GeoJSON 'Feature' object, but got type 'apex_algorithm'."
        ):
            _ = Algorithm.from_ogc_api_record(data)

    def test_from_ogc_api_record_wrong_conform(self):
        data = {
            "id": "wrong",
            "type": "Feature",
            "conformsTo": ["http://nope.test/"],
            "properties": {
                "type": "apex_algorithm",
            },
        }
        with pytest.raises(
            InvalidMetadataError,
            match=re.escape("Expected an 'OGC API - Records' record object, but got ['http://nope.test/']."),
        ):
            _ = Algorithm.from_ogc_api_record(data)

    def test_from_ogc_api_record_wrong_properties_type(self):
        data = {
            "id": "wrong",
            "type": "Feature",
            "conformsTo": ["http://www.opengis.net/spec/ogcapi-records-1/1.0/req/record-core"],
            "properties": {
                "type": "udp",
            },
        }
        with pytest.raises(InvalidMetadataError, match="Expected an APEX algorithm object, but got type 'udp'"):
            _ = Algorithm.from_ogc_api_record(data)

    def test_from_ogc_api_record_basic(self):
        data = {
            "id": "basic",
            "type": "Feature",
            "conformsTo": ["http://www.opengis.net/spec/ogcapi-records-1/1.0/req/record-core"],
            "properties": {
                "type": "apex_algorithm",
                "title": "Basic",
                "description": "The basics.",
            },
            "links": [
                {
                    "rel": "openeo-process",
                    "type": "application/json",
                    "title": "Basic UDP",
                    "href": "https://esa-apex.test/udp/basic.json",
                }
            ],
        }
        algorithm = Algorithm.from_ogc_api_record(data)
        assert algorithm.id == "basic"
        assert algorithm.title == "Basic"
        assert algorithm.description == "The basics."
        assert algorithm.udp_link == UdpLink(
            href="https://esa-apex.test/udp/basic.json",
            title="Basic UDP",
        )

    @pytest.mark.parametrize("path_type", [str, Path])
    def test_from_ogc_api_record_path(self, path_type):
        path = path_type(DATA_ROOT / "ogcapi-records/algorithm01.json")
        algorithm = Algorithm.from_ogc_api_record(path)
        assert algorithm.id == "algorithm01"
        assert algorithm.title == "Algorithm One"
        assert algorithm.description == "A first algorithm."
        assert algorithm.udp_link == UdpLink(
            href="https://esa-apex.test/udp/algorithm01.json",
            title="UDP One",
        )

    def test_from_ogc_api_record_str(self):
        dump = (DATA_ROOT / "ogcapi-records/algorithm01.json").read_text()
        algorithm = Algorithm.from_ogc_api_record(dump)
        assert algorithm.id == "algorithm01"
        assert algorithm.title == "Algorithm One"
        assert algorithm.description == "A first algorithm."
        assert algorithm.udp_link == UdpLink(
            href="https://esa-apex.test/udp/algorithm01.json",
            title="UDP One",
        )

    def test_from_ogc_api_record_url(self, requests_mock):
        url = "https://esa-apex.test/algorithms/a1.json"
        dump = (DATA_ROOT / "ogcapi-records/algorithm01.json").read_text()
        requests_mock.get(url, text=dump)
        algorithm = Algorithm.from_ogc_api_record(url)
        assert algorithm.id == "algorithm01"
        assert algorithm.title == "Algorithm One"
        assert algorithm.description == "A first algorithm."
        assert algorithm.udp_link == UdpLink(
            href="https://esa-apex.test/udp/algorithm01.json",
            title="UDP One",
        )


class TestGithubAlgorithmRepository:
    @pytest.fixture
    def repo(self) -> GithubAlgorithmRepository:
        # TODO: avoid depending on an actual GitHub repository. Mock it instead?
        #       Or run this as an integration test?
        return GithubAlgorithmRepository(
            owner="ESA-APEx",
            repo="apex_algorithms",
            folder="algorithm_catalog",
        )

    def test_list_algorithms(self, repo):
        assert repo.list_algorithms() == [
            "worldcereal.json",
        ]

    def test_get_algorithm(self, repo):
        algorithm = repo.get_algorithm("worldcereal.json")
        assert algorithm == Algorithm(
            id="worldcereal_maize",
            title="ESA worldcereal global maize detector",
            description="A maize detection algorithm.",
            udp_link=UdpLink(
                href="https://github.com/ESA-APEX/apex_algorithms/blob/main/openeo_udp/worldcereal_inference.json",
                title="openEO UDP",
            ),
        )
