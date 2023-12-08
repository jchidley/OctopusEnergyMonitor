"""The app"""
import json
import configparser as cp
from os.path import exists
from dataclasses import dataclass, field
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly
import plotly.express as px
import pandas as pd
from octopus import OctopusEnergy


def line_plot(plot_data, plot_title):
    """
    We are building a plotly chart here, using python, from python data. This
    plotly object is JSON encoded and then rehyrated at the front end.
    An alternative would be to send the raw data to the front end (probaby
    still JSON encoded) and build the chart there, using a suitalbe package.
    """
    fig = px.line(
        plot_data,
        range_y=[0, plot_data.max() * 1.1],
    ).update_layout(showlegend=False, title=plot_title)
    json_plot = plotly.io.to_json(fig)
    return json_plot


def histogram_plot(plotData, plotTitle):
    fig = px.histogram(
        plotData, x="consumption", nbins=40, range_x=[0, 20]
    ).update_layout(showlegend=False, title=plotTitle)
    json_plot = plotly.io.to_json(fig)
    return json_plot


@dataclass
class OctopusData:
    """Class for keeping track of an item in inventory."""

    agile_tariff: pd.DataFrame = field(default_factory=pd.DataFrame)
    electricity_consumption: pd.DataFrame = field(default_factory=pd.DataFrame)
    gas_consumption: pd.DataFrame = field(default_factory=pd.DataFrame)
    missing_gas: pd.DataFrame = field(default_factory=pd.DataFrame)
    missing_electric: pd.DataFrame = field(default_factory=pd.DataFrame)
    electricity_daily_chart: json = None
    electricity_rolling_chart: json = None
    gas_consumption_binned_chart: json = None
    gas_consumption_2022_binned_chart: json = None
    gas_consumption_2023_binned_chart: json = None
    gas_consumption_2024_binned_chart: json = None
    gas_daily_chart: json = None
    gas_rolling_chart: json = None

    def update(self, octopus_client):
        # error loading because...
        # https://stackoverflow.com/questions/68625748/attributeerror-cant-get-attribute-new-block-on-module-pandas-core-internal

        if exists("./agile_tariff.parquet"):
            self.agile_tariff = pd.read_parquet("./agile_tariff.parquet")
        else:
            self.agile_tariff = octopus_client.get_agile_tarriff_rates()
        if exists("./e_consumption.parquet"):
            self.electricity_consumption = pd.read_parquet("./e_consumption.parquet")
        else:
            self.electricity_consumption = octopus_client.consumption(
                OctopusEnergy.FuelType.ELECTRIC, page_size=25000
            )
        if exists("./g_consumption.parquet"):
            self.gas_consumption = pd.read_parquet("./g_consumption.parquet")
        else:
            self.gas_consumption = octopus_client.consumption(
                OctopusEnergy.FuelType.GAS, page_size=25000
            )

        self.agile_tariff = octopus_client.get_agile_tarriff_rates(self.agile_tariff)
        self.electricity_consumption = octopus_client.update_consumption(
            OctopusEnergy.FuelType.ELECTRIC, self.electricity_consumption
        )
        self.gas_consumption = octopus_client.update_consumption(
            OctopusEnergy.FuelType.GAS, self.gas_consumption
        )

        self.missing_gas = OctopusEnergy.missing(self.gas_consumption)
        self.missing_electric = OctopusEnergy.missing(self.electricity_consumption)
        self.electricity_charts()
        self.gas_charts()

        self.agile_tariff.to_parquet("./agile_tariff.parquet")
        self.electricity_consumption.to_parquet("./e_consumption.parquet")
        self.gas_consumption.to_parquet("./g_consumption.parquet")

    def electricity_charts(self):
        """A series of electricity charts based on consumption data"""
        electricity_consumption_daily = self.electricity_consumption.resample("D").sum(
            numeric_only=True
        )
        electricity_consumption_rolling = (
            self.electricity_consumption["consumption"]
            .sort_index()
            .rolling(24 * 2 * 10)
            .sum(numeric_only=True)
        )
        self.electricity_daily_chart = line_plot(
            electricity_consumption_daily, "Electricity Consumption Daily"
        )

        self.electricity_rolling_chart = line_plot(
            electricity_consumption_rolling, "Electricity Consumption Rolling"
        )

    def gas_charts(self):
        """A series of gas charts based on consumption data"""
        gas_consumption_daily = self.gas_consumption.resample("D").sum(
            numeric_only=True
        )
        gas_consumption_rolling = (
            self.gas_consumption["consumption"]
            .sort_index()
            .rolling(24 * 2 * 30)
            .sum(numeric_only=True)
        )
        # Volume correction * Calorific Value / convert from joules
        gas_conversion_factor = 1.02264 * 39.1 / 3.6
        # consumption * gasConversionFactor = kWh
        hourly = (
            octopusData.gas_consumption["consumption"]
            .resample("H")
            .sum(numeric_only=True)
        )
        gas_consumption = (
            hourly.where((hourly.index < "2021-01-01") & (hourly > 0.1))
            .sort_values(ascending=False)
            .dropna()
            * gas_conversion_factor
        )
        now = datetime.now()
        last_year = now + relativedelta(years=-1)
        # Winter 2022, after adjustment to lower flow temp in January
        gas_consumption_2022 = (
            hourly.where(
                (hourly.index > "2021-09-30")
                & (hourly.index < "2022-10-01")
                & (hourly > 0.1)
            )
            .sort_values(ascending=False)
            .dropna()
            * gas_conversion_factor
        )
        gas_consumption_2023 = (
            hourly.where(
                (hourly.index > "2022-09-30")
                & (hourly.index < "2023-10-01")
                & (hourly > 0.1)
            )
            .sort_values(ascending=False)
            .dropna()
            * gas_conversion_factor
        )
        gas_consumption_2024 = (
            hourly.where(
                (hourly.index > "2023-09-30")
                & (hourly.index < now.isoformat())
                & (hourly > 0.1)
            )
            .sort_values(ascending=False)
            .dropna()
            * gas_conversion_factor
        )

        self.gas_consumption_binned_chart = histogram_plot(
            gas_consumption, "Gas Consumption"
        )
        self.gas_consumption_2022_binned_chart = histogram_plot(
            gas_consumption_2022, "Gas Consumption 2022"
        )
        self.gas_consumption_2023_binned_chart = histogram_plot(
            gas_consumption_2023, "Gas Consumption 2023"
        )
        self.gas_consumption_2024_binned_chart = histogram_plot(
            gas_consumption_2024, "Gas Consumption 2024"
        )

        self.gas_daily_chart = line_plot(gas_consumption_daily, "Gas Consumption Daily")
        self.gas_rolling_chart = line_plot(
            gas_consumption_rolling, "Gas Consumption Rolling"
        )


cfg = cp.ConfigParser()
cfg.read_file(open("config.ini"))
# An application which requires initial values to be loaded from a file should load the required file or files using read_file() before calling read() for any optional files

# https://peps.python.org/pep-0680/
# https://vickiboykis.com/2020/02/25/securely-storing-configuration-credentials-in-a-jupyter-notebook/
# https://martin-thoma.com/configuration-files-in-python/
# https://docs.python.org/3/library/configparser.html
# https://github.com/crdoconnor/strictyaml
# https://nestedtext.org/

client = OctopusEnergy(cfg)

octopusData = OctopusData()
octopusData.update(client)
