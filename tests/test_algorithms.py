from pathlib import Path

import pytest

from esa_apex_toolbox.algorithms import Algorithm

DATA_ROOT = Path(__file__).parent / "data"


class TestAlgorithm:
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
                    "rel": "udp",
                    "type": "application/json",
                    "title": "openEO UDP",
                    "href": "https://esa-apex.test/udp/basic.json",
                }
            ],
        }
        algorithm = Algorithm.from_ogc_api_record(data)
        assert algorithm.id == "basic"
        assert algorithm.title == "Basic"
        assert algorithm.description == "The basics."

    @pytest.mark.parametrize("path_type", [str, Path])
    def test_from_ogc_api_record_path(self, path_type):
        path = path_type(DATA_ROOT / "ogcapi-records/algorithm01.json")
        algorithm = Algorithm.from_ogc_api_record(path)
        assert algorithm.id == "algorithm01"
        assert algorithm.title == "Algorithm One"
        assert algorithm.description == "A first algorithm."

    def test_from_ogc_api_record_str(self):
        dump = (DATA_ROOT / "ogcapi-records/algorithm01.json").read_text()
        algorithm = Algorithm.from_ogc_api_record(dump)
        assert algorithm.id == "algorithm01"
        assert algorithm.title == "Algorithm One"
        assert algorithm.description == "A first algorithm."

    def test_from_ogc_api_record_url(self, requests_mock):
        url = "https://esa-apex.test/algorithms/a1.json"
        dump = (DATA_ROOT / "ogcapi-records/algorithm01.json").read_text()
        requests_mock.get(url, text=dump)
        algorithm = Algorithm.from_ogc_api_record(url)
        assert algorithm.id == "algorithm01"
        assert algorithm.title == "Algorithm One"
        assert algorithm.description == "A first algorithm."
