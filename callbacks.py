from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_html_components as html 
import dash_table
import dash_table.FormatTemplate as FormatTemplate
import dash_bootstrap_components as dbc
from dash import callback_context
from flask import request
import json
from datetime import datetime as dt
from datetime import date
import pandas as pd
import numpy as np
import re  # used to regex date picker range output

from components import functions
from components import visualizations
from components.table_highlights import discrete_background_color_bins

from layouts import table_filter, semester_filter  # NEEDED?

from app import app, db  #uncomment for dev

print('starting callbacks.py')

sem_months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
                'Jan', 'Feb', 'Mar']

print ('starting data load')
# Load data 
hours_report, hours_entries = functions.import_hours()
planned_hours = functions.read_table('planned_hrs', db.engine)  # uncomment for dev
allocation_df = functions.build_allocation_table(planned_hours)

print('finished data load')
# calculate DT, semester and strategy year helper columns

# month_entries = functions.get_month_entries(hours_entries)
# month_class = functions.get_classification(month_entries)  # used for project breakdown















### SET DATE PICKER END DATE ###
@app.callback(
    Output('date-picker-range', 'end_date'),
           [Input('select-name', 'value')]
)
def update_end_date(name):
    max_DT = _get_last_valid_date(name)
    max_DT_s = max_DT.strftime('%Y-%m-%d')
    return max_DT_s    


### UPDATE ALLOCATION TAB LAYOUTS ###
@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'active_tab')])
def render_content(tab):
    # TODO: update dropdown value and options
    if tab == 'by-person':
        return html.Div([
            html.H3('Tab content 1'),
            # dbc.Row(
            #     [
            #         dbc.Col(table_filter, width=6),
            #         dbc.Col(semester_filter, width=6)
            #     ]
            # ),
            html.Br()
        ])
    elif tab == 'by-project':
        return html.Div([
            html.H3('Tab content 2'),
            # dbc.Row(
            #     [
            #         dbc.Col(table_filter, width=6),
            #         dbc.Col(semester_filter, width=6)
            #     ]
            # ),
            html.Br()
        ])
    elif tab == 'by-month':
        return html.Div([
            html.H3('Tab content 3'),
            # table_filter,
            html.Br()
        ])

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
    if active_tab in ['by-person', 'by-project']:
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
        col_format = {
            'name': str(col),
            'id': str(col),
            'deletable': False,
            'editable': True
            }
        if col in ['Project', 'User Name', 'Total', 'Sem']:
            col_format['editable'] = False
        elif col in ['% FTE']:
            col_format['editable'] = False
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
    (styles, legend) = discrete_background_color_bins(pdf, semester)
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
        style_data_conditional=styles,        
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
    # get semester and year
    sem = semester.split('|')[0].strip()
    sy = semester.split('|')[1].strip()
    sem_fte = functions.get_sem_fte(sem, sy)
    
    cols = [column['name'] for column in columns]
    col = [col for col in cols if col in ['Project', 'User Name']][0]
    # calculate Total column 
    for row in rows:
        try: 
            row['Sem'] = sum([float(val) if key not in ['Project', 'User Name', 'Sem', '% FTE'] and val else 0 for key, val in row.items()])
            row['% FTE'] = row['Sem']/sem_fte
        except:
            row['Sem'] = 0
    
    # calculate Total row
    if rows[0][col] == 'Total':
        rows[0] = {c['id']: sum([float(row[c['id']]) if c['id'] not in ['Project', 'User Name'] and row[c['id']] and row[col] != 'Total' else 0 for row in rows]) for c in columns}
        # rows[1] = {}
    else:
        # insert total row on initial load
        rows.insert(0, {c['id']: sum([float(row[c['id']]) if c['id'] not in ['Project', 'User Name'] and row[c['id']] and row[col] != 'Total' else 0 for row in rows]) for c in columns})
        # rows.insert(1, {c['id']: rows[0][c['id']]/get_month_fte(c['id'], 2020) if c['id'] in sem_months else '' for c in columns})
    # update first column to say 'total'
    for row in rows:
        if row[col] == 0:
            row[col] = 'Total'
                
    return rows


@app.callback(
    Output('allocation-table', 'style_data_conditional'),
    [Input('allocation-table', 'derived_virtual_data')],
    [State('allocation-table', 'data'),
     State('semester-filter', 'value')]
)
def style_allocation_table(timestamp, data, semester):
    df = functions.decalc_allocation_data(data)
    (styles, legend) = discrete_background_color_bins(df, semester)
    return styles

    
@app.callback(
    Output('allocation-table', 'is_focused'),  # output must not exist before creating allocation table
    [Input('save-plan', 'n_clicks')],
    [State('allocation-table', 'derived_virtual_data'),
     State('semester-filter', 'value'),
     State('table-filter', 'value')]
)
def save_to_postgres(n_clicks, data, semester, table_filter):
    if n_clicks is None:
        raise PreventUpdate
    ctx = callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    df = functions.decalc_allocation_data(data)
    col = [col for col in df.columns if col in ['Project', 'User Name']][0]
    df = df.melt(id_vars=col, var_name='Entry Month', value_name='Hours')

    sem = semester.split('|')[0].strip()
    sy = semester.split('|')[1].strip()
    base_year = int(sy[:4])

    sem_years = [base_year + helper for helper in functions.year_helper]
    df['Entry Year'] = df['Entry Month'].apply(lambda x: sem_years[functions.sem_months.index(x)])

    if button_id == 'save-plan':
        df['User Name'] = table_filter

    print(df)
        
    