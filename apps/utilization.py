from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from flask import request
from datetime import datetime as dt
import json
import pandas as pd

from components import visualizations
from apps.data import usernames, hours_report, hours_entries

from app import app

### ----------------------------- LAYOUT --------------------------------- ###

### INSTRUCTIONS ###
instruction_text = [
    'Utilization measures how much time we spend '
    'towards billable projects. Hitting your utilization target helps '
    'ensure our company is sustainable.',
    html.Br(),html.Br(),
    'Utilization is calculated as the number of billable hours divided '
    'by the workable hours in the month, regardless of your status as '
    'full-time or part-time or the total number of hours you worked.',
    html.Br(),html.Br(),
    html.B('Use the slider below to input your expected utilization for the '
    "remaining months in this strategic year. Or, return the slider to 'OFF' "
    "(0%) to use this month's utilization-to-date to predict utilization."),
    html.Br(),html.Br()
    ]

instructions = dbc.Card(
    [
        dbc.CardBody(
            [
                html.P(instruction_text)
            ]
        )
    ]
)

### DROPDOWN ###
select_name = dcc.Dropdown(
    id='select-name',
    placeholder='Begin typing to find your name',
    persistence=True,
    multi=False
)

drop_downs = dbc.Container(
    select_name
)

### RESET CHART ###
reset_chart = dbc.Button("Back", id='reset-axes',
            color='secondary', 
            outline=True, size='sm')


### UTILIZATION CHART ###
util_card = dcc.Graph(id='utilization-chart',
                      config={
                          'displayModeBar': 'hover',
                          'doubleClick': False,
                          'scrollZoom': False,
                          'modeBarButtonsToRemove': [
                              'zoom2d', 'select2d', 'lasso2d', 
                              'zoomIn2d', 'zoomOut2d', 'autoScale2d', 
                              'resetScale2d', 'hoverClosestCartesian',
                              'hoverCompareCartesian'
                              ],
                          'displaylogo': False
                          }
                      )



### SLIDER ###
util_slider = daq.Slider(
    id='util-slider',
    min=0,
    max=120,
    vertical=True,
    handleLabel={"showCurrentValue": True,"label": "%"},
    labelPosition='top',
    size=265*1.3,
    updatemode='mouseup',  #'drag' for on-the-fly updates,
    color='green',
    marks={'0': 'OFF'}
)  

utilization_display = dbc.Row(
            [
                dbc.Col(util_card, md=11, sm=11),
                dbc.Col(util_slider, md=1, sm=1)
            ], justify='center', align='center'
        )


### VALID THRU ###
valid_thru = dbc.Container(html.Div(id='valid-thru'),
                           style={'fontFamily': 'Calibri, Arial',
                                  'fontSize': 16,
                                  'textAlign': 'left'})


### UPDATE TRIGGER ###
fire_me = html.Div(id='fire', children=[], style={'display': 'none'})
'''
The fire_me layout item triggers the update of the drop down to select
a name
'''

### LAYOUT ###
layout = html.Div([
    dbc.Container(instruction_text),
    drop_downs,
    html.Br(),
    dbc.Container(reset_chart),
    dcc.Loading(dbc.Container(utilization_display)),
    html.Br(),
    valid_thru,
    html.Br(),
    fire_me
])

### ---------------------------- CALLBACKS ------------------------------- ###

### UPDATE NAME OPTIONS AND VALUE ###
@app.callback(
    [Output('select-name', 'options'),
     Output('select-name', 'value')],
    [Input('fire', 'children')]
)
def populate_names(_):
    # get list of unique names
    names = hours_report['User Name'].unique()
    names.sort()
    options = [{'label': name, 'value': name} for name in names]
    initial_user = usernames.get(request.authorization['username']) 
        
    return options, initial_user


### UPDATE UTILIZATION CHART ###
@app.callback(
    Output('utilization-chart', 'figure'),
    [Input('select-name', 'value'),
     Input('util-slider', 'value'),
     Input('reset-axes', 'n_clicks')]
)
def update_utilization_chart(name, predict_input, n_clicks):
    if name or n_clicks:
        return visualizations.plot_utilization(
            hours_report, name, predict_input
            )
    else:
        raise PreventUpdate


# UPDATE VALID THROUGH TEXT ###
def _get_last_valid_date(name):
    """returns last valid date as datetime"""
    filt = ((hours_entries['User Name'] == name) 
            & (hours_entries['Hours Date'] <= dt.today()))
    current_hours = hours_entries.loc[filt, 'Hours Date']
    max_DT = current_hours.max()
    return max_DT

@app.callback(
    Output('valid-thru', 'children'),
    [Input('select-name', 'value')]
)
def get_valid_thru(name):
    max_DT = _get_last_valid_date(name)
    max_DT_s = max_DT.strftime('%A, %B %e, %Y')
    text = f'Data valid through: {max_DT_s}'
    return text
