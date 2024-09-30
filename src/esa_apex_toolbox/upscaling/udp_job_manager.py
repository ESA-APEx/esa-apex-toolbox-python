import ast
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import shapely

import openeo
from openeo.extra.job_management import MultiBackendJobManager


class UDPJobManager(MultiBackendJobManager):
    """
    Large area processing for UDP's.

    This job manager can run complex workflows without requiring project specific dependencies.
    """
    
    def __init__(self, udp_id:str, udp_namespace:str, fixed_parameters:dict, job_options:dict=None):
        super().__init__()
        self.largescale_process = None
        self._job_options = job_options
        self.fixed_parameters = fixed_parameters
        self.udp_namespace = udp_namespace
        self.udp_id = udp_id
        self.dataframe: pd.DataFrame = None

        self._parse_udp()

    def _parse_udp(self):
        self.udp_metadata = requests.get(self.udp_namespace).json()

    @property
    def job_options(self):
        return self._job_options

    @job_options.setter
    def job_options(self, value):
        self._job_options = value

    def udp_parameters(self) -> list[dict]:
        return self.udp_metadata["parameters"]

    def udp_parameter_schema(self, name:str) -> Optional[dict]:
        return {p["name"]:p.get("schema",None) for p in self.udp_parameters()}.get(name,None)


    def add_jobs(self, jobs_dataframe):
        """
        Add jobs to the job manager.

        Column names of the dataframe have to match with UDP parameters.

        Extra columns names:

        - `title` : Title of the job
        - `description` : Description of the job

        """
        if self.dataframe is None:
            self.dataframe = jobs_dataframe
        else:
            raise ValueError("Jobs already added to the job manager.")

    def start_job_thread(self):
        """
        Start running the jobs in a separate thread, returns afterwards.
        """

        udp_parameter_names = [p["name"] for p in self.udp_parameters()]

        geojson_params = [p["name"] for p in self.udp_parameters() if
                          p.get("schema", {}).get("subtype", "") == "geojson"]


        output_file = Path("jobs.csv")
        if self.dataframe is not None:
            df = self._normalize_df(self.dataframe)

            def normalize_fixed_param_value(name, value):
                if isinstance(value, list) or isinstance(value, tuple):
                    return len(df) * [value]
                else:
                    return value

            new_columns = {
                col: normalize_fixed_param_value(col,val) for (col, val) in self.fixed_parameters.items() if col not in df.columns
            }
            new_columns["udp_id"] = self.udp_id
            new_columns["udp_namespace"] = self.udp_namespace
            print(new_columns)
            df = df.assign(**new_columns)

            if len(geojson_params) == 1:
                #TODO: this is very limited, expand to include more complex cases:
                # - bbox instead of json
                if geojson_params[0] not in df.columns:
                    df.rename_geometry(geojson_params[0],inplace=True)
            elif len(geojson_params) > 1:
                for p in geojson_params:
                    if p not in df.columns:
                        raise ValueError(f"Multiple geojson parameters, but not all are in the dataframe. Missing column: {p}, available columns: {df.columns}")

            self._persists(df, output_file)



        def start_job(
                row: pd.Series,
                connection: openeo.Connection,
                **kwargs
        ) -> openeo.BatchJob:

            def normalize_param_value(name, value):
                schema = self.udp_parameter_schema(name)
                if isinstance(value, str) and schema.get("type","") == "array":
                    return ast.literal_eval( value )
                elif isinstance(value, str) and schema.get("subtype","") == "geojson":
                    #this is a side effect of using csv + renaming geometry column
                    return shapely.geometry.mapping(shapely.wkt.loads(value))
                else:
                    return value

            parameters = {k: normalize_param_value(k,row[k]) for k in udp_parameter_names }



            cube = connection.datacube_from_process(row.udp_id,row.udp_namespace, **parameters)

            title = row.get("title", f"Subjob {row.udp_id} - {str(parameters)}")
            description = row.get("description", f"Subjob {row.udp_id} - {str(parameters)}")
            return cube.create_job(title=title, description=description)



        import multiprocessing, time

        def start_running():
            self.run_jobs(df=None, start_job=start_job, output_file=output_file)

        self.largescale_process = multiprocessing.Process(target=start_running)
        self.largescale_process.start()

    def stop_job_thread(self):
        self.largescale_process.terminate()
