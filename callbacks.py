from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from flask import request
import json

from components import functions
from components import visualizations

from app import app

# Load data 
hours_report = functions.import_hours()

### UPDATE NAMES ###
@app.callback(
    [Output('select-name', 'options'),
     Output('select-name', 'value')],
    [Input('fire', 'children')],
    [State('names_store', 'children')]
)
def populate_names(_, stored_names):
    # get list of unique names
    names = hours_report['User Name'].unique()
    names.sort()
    options = [{'label': name, 'value': name} for name in names]
    # get names
    user = request.authorization['username']
    user = 'Anderson, Erik'
    users = [user]
    
    return options, users

### UPDATE UTILIZATION CHART ###
@app.callback(
    Output('utilization-chart', 'figure'),
    [Input('select-name', 'value'),
     Input('util-slider', 'value')]
)
def update_utilization_chart(names, predict_input):
    if names:
        fig = visualizations.plot_utilization(hours_report, 
                                              names,
                                              predict_input)
    else:
        raise PreventUpdate
    
    return fig


