from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_html_components as html 
import dash_table
import dash_table.FormatTemplate as FormatTemplate
import dash_bootstrap_components as dbc
from flask import request
import json
from datetime import datetime as dt
from datetime import date
import pandas as pd
import numpy as np
import re  # used to regex date picker range output

from components import functions
from components import visualizations

from layouts import table_filter, semester_filter  # NEEDED?

from app import app  #, db  #uncomment for dev

sem_months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
                'Jan', 'Feb', 'Mar']

def get_month_fte(month, year):
    """returns fte hours given any month and year"""
    year_months = sem_months[9:] + sem_months[:9]
    month_idx = year_months.index(month)
    start_date = date(year, month_idx, 1)
    end_date = date(year, month_idx+1, 1)
    days = np.busday_count(start_date, end_date)
    hours = days * 8
    return hours
    
# Load data 
hours_report, hours_entries = functions.import_hours()
# df = functions.read_table('planned_hrs', db.engine)  # uncomment for dev
allocation_df = functions.build_allocation_table(df)

# calculate DT, semester and strategy year helper columns

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


# # update tab layouts
# @app.callback(Output('tabs-content', 'children'),
#               [Input('tabs', 'active_tab')])
# def render_content(tab):
#     # TODO: update dropdown value and options
#     if tab == 'by-person':
#         return html.Div([
#             html.H3('Tab content 1'),
#             # dbc.Row(
#             #     [
#             #         dbc.Col(table_filter, width=6),
#             #         dbc.Col(semester_filter, width=6)
#             #     ]
#             # ),
#             html.Br()
#         ])
#     elif tab == 'by-project':
#         return html.Div([
#             html.H3('Tab content 2'),
#             # dbc.Row(
#             #     [
#             #         dbc.Col(table_filter, width=6),
#             #         dbc.Col(semester_filter, width=6)
#             #     ]
#             # ),
#             html.Br()
#         ])
#     elif tab == 'by-month':
#         return html.Div([
#             html.H3('Tab content 3'),
#             # table_filter,
#             html.Br()
#         ])

# update table filter
@app.callback(
    [Output('table-filter', 'options'),
    Output('table-filter', 'value'),
    Output('hide-table-filter', 'style'),
    Output('placeholder-table-filter', 'style')],
    [Input('tabs', 'active_tab')],
    [State('initial-state', 'data')]
)
def populate_filter(active_tab, existing_name):
    if active_tab == 'by-person':
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

        return options, user, {}, {'display': 'none'}
    
    elif active_tab == 'by-project':
        # get list of unique names
        projects = hours_entries['Project'].unique()
        projects.sort()
        options = [{'label': project, 'value': project} for project in projects]
        value = projects[0]
        
        return options, value, {}, {'display': 'none'}
    
    elif active_tab == 'by-month':
        options = {'label': 'label', 'value': 'value'},
        value = 'value'
        return options, value, {'display': 'none'}, {}

# update semester filter
@app.callback(
    [Output('semester-filter', 'options'),
     Output('semester-filter', 'value')],
    [Input('tabs', 'active_tab')]
)
def populate_semester_filter(active_tab):
    if active_tab == 'by-person' or active_tab == 'by-project':
        periods = ['Sem 2 | 2020-2021', 'Sem 1 | 2020-2021',
                    'Sem 2 | 2019-2020', 'Sem 1 | 2019-2020']
        options =  [{'label': period, 'value': period}
                    for period in periods]
        value = periods[1]
    
    elif active_tab == 'by-month':
        options = [{'label': month + ' 2020', 'value': month  + ' 2020'}
                    for month in sem_months]
        value = 'Sep 2020'
    
    return options, value
    

# populate allocation table
@app.callback(
    Output('allocation-div', 'children'),
    [Input('tabs', 'active_tab'),
     Input('table-filter', 'value'),
     Input('semester-filter', 'value')]
)
def populate_table(active_tab, table_filter, semester):
    # helper function for column formatting
    def col_formatter(col):
        print('formatting')
        col_format = {
            'name': str(col),
            'id': str(col),
            'deletable': False,
            'editable': True
            }
        if col in ['Project', 'User Name', 'Total']:
            col_format['editable'] = False
        elif col in ['% FTE']:
            print('found FTE')
            col_format['type'] = 'numeric'
            col_format['format'] = FormatTemplate.percentage(0)
        else:
            col_format['type'] = 'numeric'
        
        return col_format
            
        
    # filter by person, project or month depending on active tab and
    # filter by semester/month dropdown
    if active_tab == 'by-person':
        s = semester.split('|')[0].strip()
        sy = semester.split('|')[1].strip()
        filt = ((allocation_df['User Name'] == table_filter) & 
                (allocation_df['Semester'] == s) &
                (allocation_df['Strategy Year'] == sy))
        df = allocation_df.loc[filt, :]
        # pivot months
        pdf = df.pivot(index='Project', columns='Entry Month',
                       values='Hours')
        # add columns
        if s == 'Sem 1':
            columns = sem_months[:7]
        if s == 'Sem 2':
            columns = sem_months[7:]
        for column in columns:
            if column not in pdf.columns:
                pdf[column] = None
        pdf = pdf[columns]
        pdf.reset_index(inplace=True)         
            
    elif active_tab == 'by-project':
        s = semester.split('|')[0].strip()
        sy = semester.split('|')[1].strip()
        filt = ((allocation_df['Project'] == table_filter) & 
                (allocation_df['Semester'] == s) &
                (allocation_df['Strategy Year'] == sy))
        df = allocation_df.loc[filt, :]
        # pivot months
        pdf = df.pivot(index='User Name', columns='Entry Month',
                       values='Hours')
        # add columns
        if s == 'Sem 1':
            columns = sem_months[:7]
        if s == 'Sem 2':
            columns = sem_months[7:]
        for column in columns:
            if column not in pdf.columns:
                pdf[column] = None
        pdf = pdf[columns]
        pdf.reset_index(inplace=True)
        
    elif active_tab == 'by-month':
        s = semester.split(' ')[0].strip()
        sy = semester.split(' ')[1].strip()
        filt = ((allocation_df['Entry Month'] == s) &
                (allocation_df['Entry Year'] == int(sy)))
    
        df = allocation_df.loc[filt, :]
        pdf = df.pivot(index='User Name', columns='Project',
                       values='Hours')
        pdf.reset_index(inplace=True)
        
       
    # populate table
    table_cols = pdf.columns.to_list()
    table_cols.insert(1, 'Sem')
    table_cols.insert(2, '% FTE')
    allocation_table = dash_table.DataTable(
        id='allocation-table',
        columns=[col_formatter(x) for x in table_cols],
        data=pdf.to_dict('records'),
        editable=True,
        row_deletable=False,
        sort_action="native",
        sort_mode="single",
        filter_action="native",
        style_table={'overflowY': 'auto', 'overflowX': 'auto',
                     'minWidth': '100%'},
        style_cell={'textAlign': 'center',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'font-family': 'Gill Sans MT, Arial',
                    'font-size': 14,
                    'font-color': 'darkgrey',
                    'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'right',
                'minWidth': '180px', 'width': '180px', 'maxWidth': '18s0px' 
            } for c in ['User Name', 'Project']
        ],
        style_data_conditional=[
            {'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)'}
        ],
        style_header={
                'backgroundColor': 'white',
                'fontWeight': 'bold'
            },
        page_action = 'none',  # implement back-end sorting if paging
        style_as_list_view=True,
        # tooltip_data=[
        #     {
        #         column: {'value': str(value), 'type': 'markdown'}
        #         for column, value in row.items()
        #     } for row in pdf.to_dict('rows')
        # ],
        # tooltip_duration=None,
        fixed_columns={'headers': True, 'data': 1},
        fixed_rows = {'headers': True},
    )
    if pdf.empty:
        return "No time allocations available"
    else:
        return allocation_table


@app.callback(
    Output('allocation-table', 'data'),
    [Input('allocation-table', 'data_timestamp')],
    [State('allocation-table', 'data'),
     State('allocation-table', 'columns'),
     State('semester-filter', 'value')]
)
def total_rows_and_cols(timestamp, rows, columns, semester):
    # get year
    sy = semester.split('|')[1].strip() 
    # calculate Total column 
    for row in rows:
        try: 
            row['Sem'] = sum([float(val) if key not in ['Project', 'User Name', 'Sem', '% FTE'] and val else 0 for key, val in row.items()])
            row['% FTE'] = row['Sem']/1211
        except:
            row['Sem'] = 0
    
    # calculate Total row
    print(rows)
    if rows[0]['Project'] == 'Total':
        rows[0] = {c['id']: sum([float(row[c['id']]) if c['id'] not in ['Project', 'User Name'] and row[c['id']] and row['Project'] != 'Total' else 0 for row in rows]) for c in columns}
        # rows[1] = {}
    else:
        # insert total row on initial load
        rows.insert(0, {c['id']: sum([float(row[c['id']]) if c['id'] not in ['Project', 'User Name'] and row[c['id']] and row['Project'] != 'Total' else 0 for row in rows]) for c in columns})
        # rows.insert(1, {c['id']: rows[0][c['id']]/get_month_fte(c['id'], 2020) if c['id'] in sem_months else '' for c in columns})
    # update first column to say 'total'
    for row in rows:
        if row['Project'] == 0:
            row['Project'] = 'Total'
    
    return rows

