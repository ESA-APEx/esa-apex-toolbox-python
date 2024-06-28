from time import sleep

import openeo
from openeo.extra.udp_job_manager import UDPJobManager

import geopandas as gpd

def test_create_and_start():


    params = {
        "biopar_type":"FAPAR",
        "date":["2023-05-01","2023-05-30"]
    }
    manager = UDPJobManager("BIOPAR","https://openeo.dataspace.copernicus.eu/openeo/1.1/processes/u:3e24e251-2e9a-438f-90a9-d4500e576574/BIOPAR",fixed_parameters=params)


    manager.add_jobs(LAEA_20km() )
    manager.add_backend("cdse",connection = openeo.connect("openeo.dataspace.copernicus.eu").authenticate_oidc(), parallel_jobs=1)
    manager.start_job_thread()
    print("started running")
    sleep(20)
    manager.stop_job_thread()


def LAEA_20km()->gpd.GeoDataFrame:
    countries = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'), bbox=(4, 50, 5, 52))
    df = gpd.read_file("https://artifactory.vgt.vito.be/auxdata-public/grids/LAEA-20km.gpkg",mask=countries)
    df = df.head(10)
    #udp uses 'geometry' as name for aoi
    #df.rename_geometry("polygon")
    return df
