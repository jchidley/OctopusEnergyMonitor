# https://developer.octopus.energy/docs/api/

from pathlib import Path
from os.path import exists
import math
import sys
import types
import requests
import pyarrow as pa
from pyarrow import json, concat_tables
import pyarrow.compute as pc
import pyarrow.parquet as pq
from strictyaml import load


# by default, strictyaml brings everything in as text
# cast to required types as required, or use a schema
cfg = load(Path("config.yml").read_text())


def octopus_session() -> requests.Session:
    """
    Setup session using secret api key from Octopus
    dashboard
    """
    session = requests.Session()
    session.auth = (cfg["API_KEY"], "")
    return session


def _session_get(session: requests.Session, url: str, parameters: dict) -> pa.Table:
    """
    Get octopus data and return a pyarrow table
    """
    response = session.get(url, params=parameters)
    table = table_from_binary_json(response.content)

    return table


def get_electricity_meter_consumption(
    session: requests.Session, page_size: int = 48
) -> pa.Table:
    """
    Get electric consumption data
    https://developer.octopus.energy/docs/api/#list-consumption-for-a-meter
    """
    parameters = {"page_size": page_size}
    url = f"{cfg['BASE_URL']}/v1/electricity-meter-points/{cfg['MPAN']}/meters/{cfg['E_SERIAL']}/consumption/"
    table = _session_get(session, url, parameters)
    return table


def get_gas_meter_consumption(
    session: requests.Session, page_size: int = 48
) -> pa.Table:
    """
    Get gas consumption data
    https://developer.octopus.energy/docs/api/#list-consumption-for-a-meter
    """
    parameters = {"page_size": page_size}
    url = f"{cfg['BASE_URL']}/v1/gas-meter-points/{cfg['MPRN']}/meters/{cfg['G_SERIAL']}/consumption/"
    table = _session_get(session, url, parameters)
    return table


def minimum_block_size(thing):
    """
    Set block size to the maximum of either 1MB or slightly larger than the thing size
    """
    max_thing_size = 1 << math.ceil(math.log2(sys.getsizeof(thing))) + 1
    one_mb = 1 << 20
    block_size = one_mb if (max_thing_size < one_mb) else max_thing_size
    return block_size


def table_from_binary_json(binary_json) -> pa.Table:
    """
    From the binary JSON content, build an arrow table
    """
    # This block size needs to be large enough to handle the entire JSON data
    content_block_size = minimum_block_size(binary_json)
    read_options = pa.json.ReadOptions(block_size=content_block_size)
    reader = pa.BufferReader(binary_json)
    table_from_json = pa.json.read_json(reader, read_options=read_options)
    return table_from_json


def results_table(table_from_json):
    """
    Transform the results data to a table
    """
    flattened_results = pc.list_flatten(table_from_json["results"])
    table = pa.Table.from_batches(
        [pa.RecordBatch.from_struct_array(c) for c in flattened_results.chunks]
    )
    return table


def update_data(session, data=None):
    """
    Update the data for:
    Gas consumption
    Electricity consumption
    Agile unit rates
    """

    def write_data(data):
        pq.write_table(data.agile_tariff_rates, "./agile_tariff_rates.parquet")
        pq.write_table(
            data.electricity_consumption, "./electricity_consumption.parquet"
        )
        pq.write_table(data.gas_consumption, "./gas_consumption.parquet")

    def get_remaining_data(data):
        remaining_data = data

        return remaining_data

    def get_initial_data():
        data = types.SimpleNamespace()
        if exists("./agile_tariff_rates.parquet"):
            data.agile_tariff_rates = pq.read_table("./agile_tariff_rates.parquet")
        else:
            data.agile_tariff_rates = get_agile_tarriff_rates(session, current=None)

        if exists("./electricity_consumption.parquet"):
            data.electricity_consumption = pq.read_table(
                "./electricity_consumption.parquet"
            )
        else:
            electricity_consumption = get_electricity_meter_consumption(
                session, page_size=25000
            )
            data.electricity_consumption = results_table(electricity_consumption)

        if exists("./gas_consumption.parquet"):
            data.gas_consumption = pq.read_table("./gas_consumption.parquet")
        else:
            gas_consumption = get_gas_meter_consumption(session, page_size=25000)
            data.gas_consumption = results_table(gas_consumption)

        write_data(data)
        return data

    if data is None:
        data = get_initial_data()

    gas_consumption = get_gas_meter_consumption(session)
    electricity_consumption = get_electricity_meter_consumption(session)

    write_data(data)
    return data


def electricity_meter_point(session):
    """
    https://developer.octopus.energy/docs/api/#electricity-meter-points
    """
    url = f"{cfg['BASE_URL']}/v1/electricity-meter-points/{cfg['MPAN']}/"
    return_value = session.get(url)
    return return_value.json()


def electricity_tariff_unit_rates(session, product_code, tariff_code):
    """
    https://developer.octopus.energy/docs/api/#list-tariff-charges
    """
    url = f"{cfg['BASE_URL']}/v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/"
    response = session.get(url)
    return_value = response.content
    return return_value


def agile_tariff_unit_rates(session):
    """
    Electricity unit rates for given GSP
    """
    gsp = electricity_meter_point(session)["gsp"]

    # Handle GSPs passed with leading underscore
    if len(gsp) == 2:
        gsp = gsp[1]

    return_value = electricity_tariff_unit_rates(
        session, product_code="AGILE-18-02-21", tariff_code="E-1R-AGILE-18-02-21-" + gsp
    )
    return return_value


def get_agile_tarriff_rates(session, current=None):
    """
    Get agile tarrif rates
    """
    response = agile_tariff_unit_rates(session)
    new = results_table(response)

    if current is None:
        results = new
    else:
        results = pa.concat_tables([current, new])

    # do some kind of cleanup, time limiting it.
    return results


s = octopus_session()
app_data = update_data(s, None)
