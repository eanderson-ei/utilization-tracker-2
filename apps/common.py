import dash_html_components as html
import dash_bootstrap_components as dbc
import json
import pandas as pd
import os

from components.utils import auth_gspread, load_report

from app import app

### ----------------------------- SETUP ---------------------------------- ###

client = auth_gspread()
# load hours report

print("loading hours report")
hours_report = pd.concat([
    load_report(client, 'hours-entries', '2023-table'),
    load_report(client, 'hours-entries', '2022-table'),
    # load_report(client, 'hours-entries', '2021-table')
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
hours_entries = load_report(client, 'hours-entries', '2022-hours')
# hours_entries = pd.concat([
#     load_report(client, 'hours-entries', '2023-hours'),
#     load_report(client, 'hours-entries', '2022-hours'),
#     # load_report(client, 'hours-entries', '2021-hours')
#     # load_report(client, 'hours-entries', '2019-hours')
# ])
hours_entries['Hours Date'] = pd.to_datetime(hours_entries['Hours Date'])

print("loading forecasts")
# load forecasts
forecasts = load_report(client, 'forecasts', 'forecasts')
forecasts['Person, ODC, Travel'] = forecasts['Person, ODC, Travel'].str.replace(r'\s+[A-Z]$', '', regex=True)
forecasts['period beginning'] = pd.to_datetime(forecasts['period beginning'])
filt = forecasts['Project'].str.contains('B&P', case=False, na=False)
forecasts.loc[filt, 'Project'] = 'B&P'

LOGO = app.get_asset_url('ei-logo-white.png')


### ----------------------------- LAYOUT ----------------------------------###

### NAVBAR ###
nav_items = dbc.Container([
    dbc.NavItem(dbc.NavLink('My Utilization', href='/')),
    dbc.NavItem(dbc.NavLink('My Projects', href='/my_projects')),
    dbc.NavItem(dbc.NavLink('My Team', href='/my_team')),
    dbc.NavItem(dbc.NavLink('Projections', href='/my_forecast')),
]
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=LOGO, height="30px")),
                        dbc.Col(dbc.NavbarBrand("Utilization Report", className="ml-2")),
                    ],
                    align="center",
                    no_gutters=True,
                ),
                # href="/",
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [nav_items], className="ml-auto", navbar=True
                ),
                id="navbar-collapse",
                navbar=True
            ),
        ]
    ),
    color="primary",
    dark=True,
    className="mb-5"
)


### ---------------------------- CALLBACKS ------------------------------- ###
