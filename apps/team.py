import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_table
from datetime import datetime as dt
import re  # used to regex date picker range output

from components import visualizations
from app import app
from apps.common import usernames, hours_entries

### ----------------------------- SETUP ---------------------------------- ###
task_entries = hours_entries.copy()
filt = task_entries['Project'].isin(['Overhead', 'R&D', 'G&A'])
task_entries.loc[filt, 'Project'] = task_entries.loc[filt, 'Task Name']

### ----------------------------- LAYOUT --------------------------------- ###

### INSTRUCTIONS ###
instruction_text = [
    "Track you team's effort.",
    html.Br(), html.Br(),
    html.B("Use the date selector to filter by date. "
           "Click in the bar chart to see tasks related to each person. "
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
select_project = dcc.Dropdown(
    id='select-project',
    placeholder='Begin typing to find your project',
    persistence=True,
    multi=False
)

# Date picker and select name drop down
user_input = dbc.Container(
    [
        dbc.Row(
            [dbc.Col(date_picker, sm=6, md=6, lg=4),
             dbc.Col(select_project, sm=6, md=6, lg=8)]
        )
    ]
)

# RESET CHART
reset_chart = dbc.Button("Back", id='clear-clickData-team',
            color='secondary', 
            outline=True, size='sm')

### TEAM CHART ###
team_graph = dcc.Graph(id='team-chart',
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
        dbc.Col(id='entry-table-team', width=12)
    )
)

### VALID THRU ###
valid_thru = dbc.Container(html.Div(id='valid-thru-team'),
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
    dcc.Loading(dbc.Container(team_graph)),
    html.Br(),
    entry_table,
    html.Br(),
    valid_thru,
    html.Br(),
    fire_me
])


### ---------------------------- CALLBACKS ------------------------------- ###

### UPDATE NAME OPTIONS AND VALUE ###
@app.callback(
    [Output('select-project', 'options')],
    [Input('fire', 'children')]
)
def populate_names(_):
    # get list of unique projects
    projects = task_entries['Project'].dropna().unique()
    projects.sort()
    options = [{'label': project, 'value': project} for project in projects]
        
    return [options]


### UPDATE PROJECTS CHART ###
@app.callback(
    Output('team-chart', 'figure'),
    [Input('select-project', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('team-chart', 'clickData')]
)
def update_project_chart(name, start_date, end_date, clickData):
    # parse dates from calendar
    start_date = dt.strptime(re.split('T| ', start_date)[0], '%Y-%m-%d')
    end_date = dt.strptime(re.split('T| ', end_date)[0], '%Y-%m-%d')
    
    if clickData is None:
        mode = 'Users'
        user = None
    else:
        click = clickData['points'][0]['y']
        print(click)
        if click in list(task_entries['User Name'].values):
            mode = 'Tasks'
            user = click
        elif click in list(task_entries['Task Name'].values):
            raise PreventUpdate
        
    fig = visualizations.plot_team(
                task_entries, name, start_date, end_date, mode=mode, 
                user=user
                )
    return fig


### UPDATE TABLE ###
@app.callback(
    Output('entry-table-team', 'children'),
    [Input('select-project', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('team-chart', 'clickData')]
)
def update_entry_table(project, start_date, end_date, clickData):
    # parse dates from calendar
    start_date = dt.strptime(re.split('T| ', start_date)[0], '%Y-%m-%d')
    end_date = dt.strptime(re.split('T| ', end_date)[0], '%Y-%m-%d')
    
    if project:
        filt = ((task_entries['Project'] == project) 
                & (task_entries['Hours Date'] >= start_date)
                & (task_entries['Hours Date'] <= end_date))
        if clickData:
            click = clickData['points'][0]['y']
            if click in list(task_entries['User Name'].values):
                filt = ((task_entries['Project'] == project) 
                    & (task_entries['Hours Date'] >= start_date)
                    & (task_entries['Hours Date'] <= end_date)
                    & (task_entries['User Name'] == click))
            elif click in list(task_entries['Task Name'].values):
                raise PreventUpdate               
                
        columns = ['Classification', 'User Name', 'Task Name', 'Hours Date', 
                   'Entered Hours', 'Comments']
        df = task_entries.loc[filt, columns]
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
    Output('clear-clickData-team', 'disabled'),
    [Input('team-chart', 'clickData')]
)
def enable_reset(clickData):
    return clickData is None


# reset team chart
@app.callback(
    Output('team-chart', 'clickData'),
    [Input('clear-clickData-team', 'n_clicks'),
     Input('select-project', 'value')]
)
def clear_clickData(n_clicks, project):
    if n_clicks or project:
        return None
    
# UPDATE VALID THROUGH TEXT ###
def _get_last_valid_date(project, start_date, end_date):
    """returns last valid date as datetime"""
    # get list of names who billed during the period
    filt = ((task_entries['Project'] == project) 
            & (task_entries['Hours Date'] >= start_date)
            & (task_entries['Hours Date'] <= end_date))
    pdf = task_entries.loc[filt]
    names = pdf['User Name'].unique()
    # get last entry for those who billed
    filt = ((task_entries['User Name'].isin(names)) 
            & (task_entries['Hours Date'] <= dt.today()))
    current_hours = task_entries.loc[filt]
    current_hours_by_person = current_hours.groupby('User Name')['Hours Date'].max()
    max_DT = current_hours_by_person.min()
    return max_DT

# @app.callback(
#     Output('valid-thru-team', 'children'),
#     [Input('select-project', 'value'),
#      Input('date-picker-range', 'start_date'),
#      Input('date-picker-range', 'end_date')]
# )
# def get_valid_thru(project, start_date, end_date):
#     if project and start_date and end_date:
#         max_DT = _get_last_valid_date(project, start_date, end_date)
#         max_DT_s = max_DT.strftime('%A, %B %e, %Y')
#         text = f'Data valid through: {max_DT_s}'
#         return text
