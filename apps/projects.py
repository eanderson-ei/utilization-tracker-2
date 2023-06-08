from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import dash_table
from datetime import datetime as dt
import re  # used to regex date picker range output

from components import visualizations
from app import app
from apps.common import usernames, hours_entries

### ----------------------------- SETUP ---------------------------------- ###



### ----------------------------- LAYOUT --------------------------------- ###

### INSTRUCTIONS ###
instruction_text = [
    "Explore the projects and tasks you've been working on.",
    html.Br(), html.Br(),
    html.B("Use the date selector to filter by date. "
           "Click in the bar chart to see tasks related to each project. "
           "Review time entries and comments in the table below. "
           "Click 'Back' to start over."),
    html.Br(), html.Br()
]

# DATE PICKER
date_picker = dcc.DatePickerRange(
                id='date-picker-range',
                start_date=dt.today().strftime('%Y-%m-01'),
                min_date_allowed='2019-04-01',
                end_date=dt.today().strftime('%Y-%m-%d'),
                number_of_months_shown=2,
                persistence=True,
                updatemode='singledate',
                style={'borderWidth': 0}  
                )

### DROPDOWN ###
select_name = dcc.Dropdown(
    id='select-name',
    placeholder='Begin typing to find your name',
    persistence=True,
    multi=False
)

# Date picker and select name drop down
user_input = dbc.Container(
    [
        dbc.Row(
            [dbc.Col(date_picker, sm=6, md=6, lg=4),
             dbc.Col(select_name, sm=6, md=6, lg=8)]
        )
    ]
)

# RESET CHART
reset_chart = dbc.Button("Back", id='clear-clickData',
            color='secondary', 
            outline=True, size='sm')

### PROJECTS CHART ###
projects_graph = dcc.Graph(id='projects-chart',
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

### TABLE ###
entry_table = dbc.Container(
    dbc.Row(
        dbc.Col(id='entry-table', width=12)
    )
)

### VALID THRU ###
valid_thru = dbc.Container(html.Div(id='valid-thru'),
                           style={'fontFamily': 'Gill Sans MT, Arial',
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
    user_input,
    html.Br(),
    dbc.Container(reset_chart),
    dcc.Loading(dbc.Container(projects_graph)),
    html.Br(),
    entry_table,
    html.Br(),
    valid_thru,
    html.Br(),
    fire_me
])


### ---------------------------- CALLBACKS ------------------------------- ###

### UPDATE PROJECTS CHART ###
@app.callback(
    Output('projects-chart', 'figure'),
    [Input('select-name', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('projects-chart', 'clickData')]
)
def update_project_chart(name, start_date, end_date, clickData):
    # parse dates from calendar
    start_date = dt.strptime(re.split('T| ', start_date)[0], '%Y-%m-%d')
    end_date = dt.strptime(re.split('T| ', end_date)[0], '%Y-%m-%d')
    
    if clickData is None:
        mode = 'Projects'
        project = None
    else:
        click = clickData['points'][0]['y']
        if click in list(hours_entries['Project'].values):
            mode = 'Tasks'
            project = click
        elif click in list(hours_entries['Task Name'].values):
            raise PreventUpdate
        
    fig = visualizations.plot_projects(
                hours_entries, name, start_date, end_date, mode=mode, 
                project=project
                )
    return fig


### UPDATE TABLE ###
@app.callback(
    Output('entry-table', 'children'),
    [Input('select-name', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('projects-chart', 'clickData')]
)
def update_entry_table(name, start_date, end_date, clickData):
    # parse dates from calendar
    start_date = dt.strptime(re.split('T| ', start_date)[0], '%Y-%m-%d')
    end_date = dt.strptime(re.split('T| ', end_date)[0], '%Y-%m-%d')
    
    if name:
        filt = ((hours_entries['User Name'] == name) 
                & (hours_entries['Hours Date'] >= start_date)
                & (hours_entries['Hours Date'] <= end_date))
        if clickData:
            click = clickData['points'][0]['y']
            if click in list(hours_entries['Project'].values):
                filt = ((hours_entries['User Name'] == name) 
                    & (hours_entries['Hours Date'] >= start_date)
                    & (hours_entries['Hours Date'] <= end_date)
                    & (hours_entries['Project'] == click))
            elif click in list(hours_entries['Task Name'].values):
                raise PreventUpdate
                # filt = ((hours_entries['User Name'] == name) 
                #     & (hours_entries['Hours Date'] >= start_date)
                #     & (hours_entries['Hours Date'] <= end_date)
                #     & (hours_entries['Task Name'] == click))               
                
        columns = ['Classification', 'Project', 'Task Name', 'Hours Date', 
                   'Entered Hours', 'Comments']
        df = hours_entries.loc[filt, columns]
        df.sort_values('Hours Date', ascending=False, inplace=True)
        df['Hours Date'] = df['Hours Date'].dt.date
        
        table = dash_table.DataTable(
            columns = [{"name": i, "id": i} for i in df.columns],
            data = df.to_dict('records'),
            filter_action='native',
            sort_action='native',
            sort_mode='multi',
            style_cell={
                'whiteSpace': 'normal',
                'height': 'auto',
                'minWidth': '30px', 'width': '30px', 'maxWidth': '30px',
                'textAlign': 'center',
                'font-family': 'Gill Sans MT, Arial',
                'font-size': 14,
                'font-color': 'darkgrey'
            },
            style_header={
                'backgroundColor': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {'if': {'row_index': 'odd'},
                 'backgroundColor': 'rgb(248, 248, 248)'},
                # {'if': {'column_id': 'Task ID'},
                # 'width': '15%'},
                # {'if': {'column_id': 'Task Name'},
                # 'width': '25%'},
                # {'if': {'column_id': 'Hours Date'},
                # 'width': '15%'},
                # {'if': {'column_id': 'Entered Hours'},
                # 'width': '15%'},
                {'if': {'column_id': 'Comments'},
                'width': '60px','textAlign': 'left'}
            ],
            page_action = 'none',  # implement back-end sorting if paging
            fixed_rows = {'headers': True},
            style_table={'height': '500px', 
                         'overflowY': 'auto',
                         'overflowX': 'auto'},
            style_as_list_view=True,
        )
        
        return table

# enable reset button
@app.callback(
    Output('clear-clickData', 'disabled'),
    [Input('projects-chart', 'clickData')]
)
def enable_reset(clickData):
    return clickData is None


# reset projects chart
@app.callback(
    Output('projects-chart', 'clickData'),
    [Input('clear-clickData', 'n_clicks'),
     Input('select-name', 'value')]
)
def clear_clickData(n_clicks, name):
    if n_clicks or name:
        return None