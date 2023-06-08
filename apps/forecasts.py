from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from apps.common import forecasts
from components import visualizations
from app import app

### ----------------------------- SETUP ---------------------------------- ###



### ----------------------------- LAYOUT --------------------------------- ###

### INSTRUCTIONS ###
instruction_text = [
    "Visualize level of effort forecasts from the Resource Planning process.",
    html.Br(), html.Br(),
    html.B("Select your name from the dropdown menu"),
    html.Br(), html.Br()
]

### DROPDOWN ###
select_name = dcc.Dropdown(
    id='select-name',
    placeholder='Begin typing to find your name',
    persistence=True,
    multi=False
)

# Date picker and select name drop down
user_input = dbc.Container(
    select_name
)

# RESET CHART
# reset_chart = dbc.Button("Back", id='clear-clickData',
#             color='secondary', 
#             outline=True, size='sm')

### PROJECTS CHART ###
forecast_graph = dcc.Graph(id='forecast-chart',
                          config={'displayModeBar': False,
                                  'doubleClick': False,
                                  'scrollZoom': False,
                                  'modeBarButtonsToRemove': [
                                       'zoom2d', 'select2d', 'lasso2d', 
                                      'zoomIn2d', 'zoomOut2d', 'autoScale2d', 
                                      'resetScale2d', 'hoverClosestCartesian',
                                      'hoverCompareCartesian'
                                      ],
                                  'displaylogo': False}
                          )

# ### TABLE ###
# entry_table = dbc.Container(
#     dbc.Row(
#         dbc.Col(id='entry-table', width=12)
#     )
# )

# ### VALID THRU ###
# valid_thru = dbc.Container(html.Div(id='valid-thru'),
#                            style={'fontFamily': 'Gill Sans MT, Arial',
#                                   'fontSize': 16,
#                                   'textAlign': 'left'})

### UPDATE TRIGGER ###
fire_me = html.Div(id='fire', children=[], style={'display': 'none'})
'''
The fire_me layout item triggers the update of the drop down to select
a name
'''

### LAYOUT ###
layout = html.Div([
    dbc.Container(instruction_text),
    user_input,
    html.Br(),
    # dbc.Container(reset_chart),
    dcc.Loading(dbc.Container(forecast_graph)),
    html.Br(),
    # entry_table,
    html.Br(),
    # valid_thru,
    html.Br(),
    fire_me
])


### ---------------------------- CALLBACKS ------------------------------- ###

### UPDATE PROJECTS CHART ###
@app.callback(
    Output('forecast-chart', 'figure'),
    [Input('select-name', 'value')]
)
def update_forecast_chart(name):        
    fig = visualizations.plot_projections(
                forecasts, name
                )
    return fig