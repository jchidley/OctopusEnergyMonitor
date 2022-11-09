import pickle
import configparser as cp
import pandas as pd
import json
import plotly
import plotly.express as px

# needs to come after the px import otherwise we get a Nonetype error with the px import
from octopus import OctopusEnergy
from dataclasses import dataclass


def linePlot(plotData, plotTitle):
    """
    We are building a plotly chart here, using python, from python data. This plotly object is JSON encoded and then rehyrated at the front end.
    An alternative would be to send the raw data to the front end (probaby still JSON encoded) and build the chart there, using a suitalbe package.
    """
    fig = px.line(
        plotData,
        range_y=[0, plotData.max() * 1.1],
    ).update_layout(showlegend=False, title=plotTitle)
    jsonPlot = plotly.io.to_json(fig)
    # an alternative way of encoding.
    # jsonPlot = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    # To use a custom JSONEncoder subclass (e.g. one that overrides the default() method to serialize additional types), specify it with the cls kwarg; otherwise JSONEncoder is used.
    return jsonPlot


def histogramPlot(plotData, plotTitle):
    fig = px.histogram(
        plotData, x="consumption", nbins=40, range_x=[0, 20]
    ).update_layout(showlegend=False, title=plotTitle)
    jsonPlot = plotly.io.to_json(fig)
    return jsonPlot


@dataclass
class OctopusData:
    """Class for keeping track of an item in inventory."""

    agile_tariff: pd.DataFrame = pd.DataFrame()
    e_consumption: pd.DataFrame = pd.DataFrame()
    g_consumption: pd.DataFrame = pd.DataFrame()
    missing_gas: pd.DataFrame = pd.DataFrame()
    missing_electric: pd.DataFrame = pd.DataFrame()
    electricityDailyChart: json = None
    electricityRollingChart: json = None
    gasConsumption2022BinnedChart: json = None
    gasConsumption2023BinnedChart: json = None
    gasDailyChart: json = None
    gasRollingChart: json = None

    def update(self, client):
        # error loading because...
        # https://stackoverflow.com/questions/68625748/attributeerror-cant-get-attribute-new-block-on-module-pandas-core-internal
        try:
            self.agile_tariff = pickle.load(open("agile_tariff.p", "rb"))
        except AttributeError:
            self.agile_tariff = client.getAgileTarriffRates()
        try:
            self.e_consumption = pickle.load(open("e_consumption.p", "rb"))
        except AttributeError:
            self.e_consumption = client.consumption(
                OctopusEnergy.FuelType.ELECTRIC, page_size=25000
            )
        try:
            self.g_consumption = pickle.load(open("g_consumption.p", "rb"))
        except AttributeError:
            self.g_consumption = client.consumption(
                OctopusEnergy.FuelType.GAS, page_size=25000
            )

        self.e_consumption = client.update_consumption(
            OctopusEnergy.FuelType.ELECTRIC, self.e_consumption
        )
        self.g_consumption = client.update_consumption(
            OctopusEnergy.FuelType.GAS, self.g_consumption
        )
        self.agile_tariff = client.getAgileTarriffRates(self.agile_tariff)

        self.missing_gas = OctopusEnergy.missing(self.g_consumption)
        self.missing_electric = OctopusEnergy.missing(self.e_consumption)
        self.electricityCharts()
        self.gasCharts()

    def electricityCharts(self):
        electricityConsumptionDaily = self.e_consumption.resample("D").sum()
        electricityConsumptionRolling = (
            self.e_consumption["consumption"].sort_index().rolling(24 * 2 * 10).sum()
        )
        self.electricityDailyChart = linePlot(
            electricityConsumptionDaily, "Electricity Consumption Daily"
        )

        self.electricityRollingChart = linePlot(
            electricityConsumptionRolling, "Electricity Consumption Rolling"
        )

    def gasCharts(self):
        gasConsumptionDaily = self.g_consumption.resample("D").sum()
        gasConsumptionRolling = (
            self.g_consumption["consumption"].sort_index().rolling(24 * 2 * 10).sum()
        )
        # Volume correction * Calorific Value / convert from joules
        gasConversionFactor = 1.02264 * 39.1 / 3.6
        # consumption * gasConversionFactor = kWh
        hourly = octopusData.g_consumption["consumption"].resample("H").sum()
        gasConsumption = (
            hourly.where((hourly.index < "01-1-2022") & (hourly > 0.1))
            .sort_values(ascending=False)
            .dropna()
            * gasConversionFactor
        )
        # Winter 2022, after adjustment to lower flow temp in January
        gasConsumption2022 = (
            hourly.where((hourly.index > "30-09-2021") & (hourly.index < "01-10-2022") & (hourly > 0.1))
            .sort_values(ascending=False)
            .dropna()
            * gasConversionFactor
        )
        gasConsumption2023 = (
            hourly.where((hourly.index > "30-09-2022") & (hourly.index < "01-10-2023") & (hourly > 0.1))
            .sort_values(ascending=False)
            .dropna()
            * gasConversionFactor
        )

        self.gasConsumptionBinnedChart = histogramPlot(
            gasConsumption, "Gas Consumption"
        )
        self.gasConsumption2022BinnedChart = histogramPlot(
            gasConsumption2022, "Gas Consumption 2022"
        )
        self.gasConsumption2023BinnedChart = histogramPlot(
            gasConsumption2023, "Gas Consumption 2023"
        )

        self.gasDailyChart = linePlot(gasConsumptionDaily, "Gas Consumption Daily")
        self.gasRollingChart = linePlot(
            gasConsumptionRolling, "Gas Consumption Rolling"
        )


# change to use TOML as this will be part of the standard lib in 3.11
# can use 'tomli' library in the meantime ('tomllib' will be based on this)

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
