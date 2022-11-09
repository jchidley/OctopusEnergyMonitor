import app
import pandas as pd
import datetime as dt

weekly = app.octopusData.g_consumption["consumption"].resample("W").sum()
print(weekly.to_csv("weekly.csv", date_format='%Y-%m-%d'))