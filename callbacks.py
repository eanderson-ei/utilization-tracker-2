from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_table
from flask import request
import json

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
    [State('names_store', 'children')]
)
def populate_names(_, stored_names):
    usernames = {
        'eanderson@enviroincentives.com': 'Anderson, Erik',
        'kboysen@enviroincentives.com': 'Boysen, Kristen',
        'kriley@enviroincentives.com': 'Riley, Kathryn',
        'cpraul@enviroincentives.com': 'Praul, Chad'
    }
    # get list of unique names
    names = hours_report['User Name'].unique()
    names.sort()
    options = [{'label': name, 'value': name} for name in names]
    # get names
    user = request.authorization['username']
    user = usernames.get(user, None)
    
    return options, user

### UPDATE UTILIZATION CHART ###
@app.callback(
    Output('utilization-chart', 'figure'),
    [Input('select-name', 'value'),
     Input('util-slider', 'value')]
)
def update_utilization_chart(name, predict_input):
    if name:
        fig = visualizations.plot_utilization(hours_report, 
                                              name,
                                              predict_input,
                                              hours_entries)  # add month_class for project breakdown
    else:
        raise PreventUpdate
    
    return fig


### UPDATE TABLE ###
@app.callback(
    Output('entry-table', 'children'),
    [Input('select-name', 'value')]
)
def update_entry_table(name):
    if name:
        filt = ((hours_entries['User Name'] == name) 
                & (hours_entries['Hours Date'] >= '2020-06-01'))
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
