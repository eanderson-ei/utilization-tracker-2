from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_table
from flask import request
import json
from datetime import datetime as dt
import re  # used to regex date picker range output

from components import functions
from components import visualizations

from app import app

# Load data 
hours_report, hours_entries = functions.import_hours()
# month_entries = functions.get_month_entries(hours_entries)
# month_class = functions.get_classification(month_entries)  # used for project breakdown

### UPDATE NAMES ###
@app.callback(
    [Output('select-name', 'options'),
     Output('select-name', 'value')],
    [Input('fire', 'children')],
     [State('initial-state', 'data')]
)
def populate_names(_, existing_name):
    with open('components/usernames.json') as f:
        usernames = json.load(f)
    # get list of unique names
    names = hours_report['User Name'].unique()
    names.sort()
    options = [{'label': name, 'value': name} for name in names]
    # get names
    user = request.authorization['username']
    user = usernames.get(user, None)
    
    if not existing_name:
        user = request.authorization['username']
        user = usernames.get(user, None)
        
    else:
        user = existing_name
        
    return options, user


@app.callback(
    Output('initial-state', 'data'),
    [Input('select-name', 'value')]
)
def store_name(name):
    if name:
        return name

### UPDATE UTILIZATION CHART ###
@app.callback(
    Output('utilization-chart', 'figure'),
    [Input('select-name', 'value'),
     Input('util-slider', 'value'),
     Input('reset-axes', 'n_clicks')]
)
def update_utilization_chart(name, predict_input, n_clicks):
    if name:
        fig = visualizations.plot_utilization(hours_report, 
                                              name,
                                              predict_input,
                                              hours_entries)  # add month_class for project breakdown
    else:
        raise PreventUpdate
    
    if n_clicks:
        fig = visualizations.plot_utilization(hours_report, 
                                              name,
                                              predict_input,
                                              hours_entries)
    
    return fig


### UPDATE PROJECTS CHART
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
    
        fig = visualizations.plot_projects(
            hours_entries, name, start_date, end_date, mode='Projects'
            )
    else:
        click = clickData['points'][0]['y']
        if click in list(hours_entries['Project'].values):
            fig = visualizations.plot_projects(
                hours_entries, name, start_date, end_date, mode='Tasks', project=click
                )
        elif click in list(hours_entries['Task Name'].values):
            raise PreventUpdate
        
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
                filt = ((hours_entries['User Name'] == name) 
                    & (hours_entries['Hours Date'] >= start_date)
                    & (hours_entries['Hours Date'] <= end_date)
                    & (hours_entries['Task Name'] == click))               
                
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
    if clickData is None:
        return True
    else:
        return False


# reset projects chart
@app.callback(
    Output('projects-chart', 'clickData'),
    [Input('clear-clickData', 'n_clicks')]
)
def clear_clickData(n_clicks):
    if n_clicks:
        return None


# update valid thru
@app.callback(
    Output('valid-thru', 'children'),
    [Input('select-name', 'value')]
)
def get_valid_thru(name):
    filt = ((hours_entries['User Name'] == name) 
            & (hours_entries['Hours Date'] <= dt.today()))
    current_hours = hours_entries.loc[filt, 'Hours Date']
    max_DT = current_hours.max()
    max_DT_s = max_DT.strftime('%A, %B %e, %Y')
    text = f'Data valid through: {max_DT_s}'
    print(text)
    return text

# @app.callback(
#     [Output('select-name2', 'options'),
#     Output('select-name2', 'value')],
#     [Input('fire', 'children')]
# )
# def populate_names2(_, stored_names):
#     usernames = {
#         'eanderson@enviroincentives.com': 'Anderson, Erik',
#         'kboysen@enviroincentives.com': 'Boysen, Kristen',
#         'kriley@enviroincentives.com': 'Riley, Kathryn',
#         'cpraul@enviroincentives.com': 'Praul, Chad'
#     }
#     # get list of unique names
#     names = hours_report['User Name'].unique()
#     names.sort()
#     options = [{'label': name, 'value': name} for name in names]
#     # get names
#     user = request.authorization['username']
#     user = usernames.get(user, None)
    
#     return options, user
