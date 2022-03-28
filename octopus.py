# Modified from
# https://gist.github.com/codeinthehole/5f274f46b5798f435e6984397f1abb64
# Requires the requests library (install with 'pip install requests')
import requests
import pandas as pd
from enum import Enum, auto


class OctopusEnergy(object):
    BASE_URL = "https://api.octopus.energy/v1"

    class DataUnavailable(Exception):
        """
        Catch-all exception indicating we can't get data back from the API
        """

    def __init__(self, cfg):
        """
        Get the configuration data https://octopus.energy/dashboard/developer/.  This includes:

        API key                             API_KEY = sk_live_ZZh...
        account number                      ACCOUNT_NUMBER = A-D...
        electricity meter-point MPAN        MPAN = 101...
        electricity meter serial number     E_SERIAL = 19L...
        gas meter-point MPRN                MPRN = 305...
        gas meter serial number             G_SERIAL = E6S...
        """

        self.cfg = cfg
        self.session = requests.Session()

    def _get(self, path, params=None):
        """
        Make a GET HTTP request
        """
        if params is None:
            params = {}
        url = self.BASE_URL + path
        try:
            response = self.session.request(
                method="GET",
                url=url,
                auth=(self.cfg["octopus"]["api_key"], ""),
                params=params,
            )
        except requests.RequestException as e:
            raise self.DataUnavailable("Network exception") from e

        if response.status_code != 200:
            raise self.DataUnavailable(
                "Unexpected response status (%s)" % response.status_code
            )

        return response.json()

    def electricity_meter_point(self):
        # See https://developer.octopus.energy/docs/api/#electricity-meter-points
        return self._get("/electricity-meter-points/%s/" % self.cfg["octopus"]["mpan"])

    def electricity_tariff_unit_rates(self, product_code, tariff_code, params=None):
        # See https://developer.octopus.energy/docs/api/#list-tariff-charges
        return self._get(
            "/products/%s/electricity-tariffs/%s/standard-unit-rates/"
            % (product_code, tariff_code),
            params=params,
        )

    def electricity_tariff_standing_charges(self, product_code, tariff_code, **params):
        # See https://developer.octopus.energy/docs/api/#list-tariff-charges
        return self._get(
            "/products/%s/electricity-tariffs/%s/standing-charges/"
            % (product_code, tariff_code),
            params=params,
        )

    def agile_tariff_unit_rates(self, **params):
        """
        Helper method to easily look-up the electricity unit rates for given GSP
        """
        gsp = self.electricity_meter_point()["gsp"]

        # Handle GSPs passed with leading underscore
        if len(gsp) == 2:
            gsp = gsp[1]
        assert gsp in (
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "P",
            "N",
            "J",
            "H",
            "K",
            "L",
            "M",
        )

        return self.electricity_tariff_unit_rates(
            product_code="AGILE-18-02-21",
            tariff_code="E-1R-AGILE-18-02-21-%s" % gsp,
            params=params,
        )

    def electricity_meter_consumption(self, **params):
        # See https://developer.octopus.energy/docs/api/#list-consumption-for-a-meter
        return self._get(
            "/electricity-meter-points/%s/meters/%s/consumption/"
            % (self.cfg["octopus"]["mpan"], self.cfg["octopus"]["e_serial"]),
            params=params,
        )

    def gas_meter_consumption(self, **params):
        # See https://developer.octopus.energy/docs/api/#list-consumption-for-a-meter
        return self._get(
            "/gas-meter-points/%s/meters/%s/consumption/"
            % (self.cfg["octopus"]["mprn"], self.cfg["octopus"]["g_serial"]),
            params=params,
        )

    class FuelType(Enum):
        ELECTRIC = auto()
        GAS = auto()

    def getAgileTarriffRates(
        self, current_agile_rates=pd.DataFrame([]), page_size=1500
    ):
        response = self.agile_tariff_unit_rates(page_size=page_size)
        results = pd.DataFrame(response["results"])
        dt = pd.to_datetime(results["valid_from"], utc=True)
        dti = pd.DatetimeIndex(dt)
        results_reindex = results.set_index(dti).drop("valid_from", axis=1)
        # agile_tariff["valid_from"] = pd.to_datetime(agile_tariff["valid_from"]) # to date only .apply(lambda a: pd.to_datetime(a).date()) # for excel
        results_reindex.loc[:, "valid_to"] = pd.to_datetime(results_reindex["valid_to"])

        agile_tariff = pd.concat([results_reindex, current_agile_rates])

        return agile_tariff.dropna().drop_duplicates()

    def missing(consumption):

        first = consumption.index.min()
        last = consumption.index.max()
        total = pd.date_range(first, last, freq="30 min")
        missing = total.difference(consumption.index)
        return missing

    def consumption(self, fuel=None, current_consumption=pd.DataFrame([]), **params):
        def consumption_from_response(response):
            results = pd.DataFrame(response["results"]).dropna().drop_duplicates()
            dt = pd.to_datetime(results["interval_start"], utc=True)
            dti = pd.DatetimeIndex(dt)
            new_consumption = results.set_index(dti).drop("interval_start", axis=1)
            # needs to be forced to UTC? otherwise treats it as an object
            new_consumption["interval_end"] = pd.to_datetime(
                new_consumption["interval_end"], utc=True
            )
            # https://stackoverflow.com/questions/55385497/how-can-i-convert-my-datetime-column-in-pandas-all-to-the-same-timezone
            # https://stackoverflow.com/questions/63495502/creating-pandas-datetimeindex-in-dataframe-from-dst-aware-datetime-objects
            # https://queirozf.com/entries/pandas-time-series-examples-datetimeindex-periodindex-and-timedeltaindex
            return new_consumption.dropna().drop_duplicates()

        if fuel == self.FuelType.ELECTRIC:
            # https://treyhunner.com/2018/10/asterisks-in-python-what-they-are-and-how-to-use-them/
            # When calling a function, the * operator can be used to unpack an iterable into the arguments in the function call:
            # The ** operator does something similar, but with keyword arguments. The ** operator allows us to take a dictionary of key-value pairs and unpack it into keyword arguments in a function call.
            response = self.electricity_meter_consumption(**params)

        if fuel is self.FuelType.GAS:
            response = self.gas_meter_consumption(**params)

        new_consumption = consumption_from_response(response)
        consumption = pd.concat([new_consumption, current_consumption])

        return consumption.dropna().drop_duplicates().sort_index()

    def update_consumption(
        self, fuel=FuelType.ELECTRIC, original_consumption=pd.DataFrame([])
    ):
        """
        Assume that there is a single contiguous block of readings (with some missing). Build upwards from that before starting to build downwards. If there is not data, get some first.
        """

        max_page_size = int(self.cfg["octopus"]["CONSUMPTION_PAGE_SIZE"])
        octopus_join_datetime = pd.to_datetime(
            self.cfg["octopus"]["OCTOPUS_JOIN_DATETIME"], utc=True
        )
        now = pd.Timestamp.now(tz="utc")

        if original_consumption.empty:
            original_consumption = self.consumption(fuel, page_size=max_page_size)

        original_max = original_consumption.index.max()
        original_min = original_consumption.index.min()

        def additionalConsuption(min_time, max_time):

            new_consumption = pd.DataFrame([])

            previous_min = max_time
            new_min = min_time

            while (new_min < previous_min) and (max_time > min_time):
                previous_min = new_min
                old_consumption = new_consumption
                new_consumption = self.consumption(
                    fuel,
                    period_from=min_time.isoformat(),
                    period_to=max_time.isoformat(),
                    page_size=max_page_size,
                )
                new_consumption = (
                    pd.concat([old_consumption, new_consumption])
                    .dropna()
                    .drop_duplicates()
                )
                new_min = new_consumption.index.min()

            return new_consumption

        newerConsumption = additionalConsuption(original_max, now)
        olderConsumption = additionalConsuption(octopus_join_datetime, original_min)

        new_consumption = pd.concat(
            [olderConsumption, original_consumption, newerConsumption]
        )

        return new_consumption.dropna().drop_duplicates().sort_index()

    def gasCost(g_consumption, start_date, end_date):
        selection = g_consumption[
            (g_consumption.index > start_date) & (g_consumption.index < end_date)
        ]
        # print(f"{selection.head(2)}\n{selection.tail(2)}")
        c = selection["consumption"].sum()
        kWh = (c * 1.02265 * 39.3) / 3.6
        standingCharge = 18.7 / 100
        unitCost = 2.74 / 100
        cost = 30 * standingCharge + kWh * unitCost
        print(f"{c:.1f} kWh \t£{cost * 1.05:.2f}")
