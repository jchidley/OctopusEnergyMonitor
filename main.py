from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from app import octopusData, client, linePlot

app = FastAPI()

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

# assumes a suitable web server, e.g. "python -m http.server 9000"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    octopusData.update(client)
    data = {
        "missing_electric": len(octopusData.missing_electric),
        "missing_gas": len(octopusData.missing_gas),
        "recent_gas": octopusData.g_consumption.index.max().isoformat(),
        "recent_electric": octopusData.e_consumption.index.max().isoformat(),
    }
    return data


@app.get("/starttimes")
def starttimes():
    octopusData.update(client)

    now = pd.Timestamp.now(tz="UTC")
    today = octopusData.agile_tariff[octopusData.agile_tariff.index >= now]

    def applicanceData(usagePattern, title):
        startTime = (
            today["value_inc_vat"]
            .rolling(len(usagePattern))
            .apply(lambda x: np.multiply(x, usagePattern).sum())
        )

        start = startTime.idxmin()
        end = start + pd.Timedelta("30 m") * len(usagePattern)
        cost = startTime.min()
        plot = linePlot(startTime, title)

        appData = {
            "start": start,
            "end": end,
            "cost": cost,
            "plot": plot,
        }

        return appData

    # order must match time order of series. latest to earliest, for instance
    washing_machine = [0.2, 0.2, 0.2, 0.2, 0.2, 1, 1]
    washing_machine_data = applicanceData(
        washing_machine, "Start Times Washing Machine"
    )

    washing_up = (
        (4.18 * 8 * 2 * 30)  # 8 litres per bowl, 2 bowls
        / (60 * 60)  # temperature difference. J/g/°C
        / (0.8)  # seconds. This gives kWh
    )  # efficiency
    unitCost = 2.74 / 100

    # 0.9 kwH over 2:44. But actually 1/2 in the first 1/2 hour, delayed by 20min, 1/2 1 hour later.
    # order must match time order of series. latest to earliest, for instance
    gentle_dishwasher = [0.4, 0, 0.5]
    gentle_dishwasher_data = applicanceData(
        gentle_dishwasher, "Start Times Gentle Dishwasher"
    )

    # 0.75 kWh over 3:58
    eco_dishwasher = [0.05, 0.05, 0.05, 0.05, 0.15, 0.15, 0.15, 0.1]
    eco_dishwasher_data = applicanceData(eco_dishwasher, "Start Times Eco Dishwasher")

    # 1.35 kWh over 3.11 hours
    intense_dishwasher = [0.05, 0.1, 0.1, 0.1, 0.1, 0.5, 0.4]
    intense_dishwasher_data = applicanceData(
        intense_dishwasher, "Start Times Intense Dishwasher"
    )

    data = {
        "WashingMachineEnd": washing_machine_data["end"],
        "WashingMachineCost": washing_machine_data["cost"],
        "WashingMachinePlot": washing_machine_data["plot"],
        "GentleDishwasherStart": gentle_dishwasher_data["start"],
        "GentleDishwasherCost": gentle_dishwasher_data["cost"],
        "GentleDishwasherPlot": gentle_dishwasher_data["plot"],
        "EcoDishwasherStart": eco_dishwasher_data["start"],
        "EcoDishwasherCost": eco_dishwasher_data["cost"],
        "EcoDishwasherPlot": eco_dishwasher_data["plot"],
        "IntenseDishwasherStart": intense_dishwasher_data["start"],
        "IntenseDishwasherCost": intense_dishwasher_data["cost"],
        "IntenseDishwasherPlot": intense_dishwasher_data["plot"],
    }
    return data


@app.get("/consumption")
def consumption():
    octopusData.update(client)

    data = {
        "gasConsumptionBinnedChart": octopusData.gasConsumptionBinnedChart,
        "gasConsumption2022BinnedChart": octopusData.gasConsumption2022BinnedChart,
        "electricityDailyChart": octopusData.electricityDailyChart,
        "electricityRollingChart": octopusData.electricityRollingChart,
        "gasDailyChart": octopusData.gasDailyChart,
        "gasRollingChart": octopusData.gasRollingChart,
    }
    return data
