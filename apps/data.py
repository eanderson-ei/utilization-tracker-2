import json
import pandas as pd
import os

from components.utils import auth_gspread, load_report

### ----------------------------- SETUP ---------------------------------- ###

client = auth_gspread()
# load hours report

print("loading hours report")
hours_report = pd.concat([
    load_report(client, 'hours-entries', '2024-table'),
    load_report(client, 'hours-entries', '2023-table'),
    load_report(client, 'hours-entries', '2022-table')
    # load_report(client, 'hours-entries', '2021-table'),
    # load_report(client, 'hours-entries', '2019-table')
])  #TODO Exceeds memory of 550Mb
hours_report['DT'] = pd.to_datetime(hours_report['DT'])
    
# load usernames
try:
    with open('components/usernames.json') as f:
        usernames = json.load(f)
# Heroku dev
except:
    json_users = os.environ.get("VALID_USERNAMES")
    usernames = json.loads(json_users)

print("loading hours entries")
# load hours entries
# hours_entries = load_report(client, 'hours-entries', '2023-hours')
hours_entries = pd.concat([
    load_report(client, 'hours-entries', '2024-hours'),
    load_report(client, 'hours-entries', '2023-hours'),
    load_report(client, 'hours-entries', '2022-hours')
    # load_report(client, 'hours-entries', '2021-hours'),
    # load_report(client, 'hours-entries', '2019-hours')
])
hours_entries['Hours Date'] = pd.to_datetime(hours_entries['Hours Date'])

print("loading forecasts")
# load forecasts
forecasts = load_report(client, 'forecasts', 'forecasts')
forecasts['Person, ODC, Travel'] = forecasts['Person, ODC, Travel'].str.replace(r'\s+[A-Z]$', '', regex=True)
forecasts['period beginning'] = pd.to_datetime(forecasts['period beginning'])
filt = forecasts['Project'].str.contains('B&P', case=False, na=False)
forecasts.loc[filt, 'Project'] = 'B&P'
