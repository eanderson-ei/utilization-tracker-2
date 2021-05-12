import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import dash_daq as daq
from datetime import datetime as dt

from components import functions

from app import app

### COMPONENTS ###
### NAV BAR ###
### FORM ###
### DROPDOWN ###
### UTILIZATION CHART ###
### WEEKLY BAN ###
### MONTHLY BURN RATE ###

print('starting layouts.py')
print('starting hidden divs')
### DIV STORES ###
hours_report = html.Div(id='hours-report', style={'display': 'none'})





print('finished hidden divs')

### INTERVAL ###
# interval = dcc.Interval(id='interval_pg', interval=86400000*7, n_intervals=0)  # activated once per week or on refresh






### My Projects Layout ###


### Allocation layout
tabs = dcc.Tabs(id='tabs', value='tab-1', children=[
    dcc.Tab(label='by Person', value='by-person'),
    dcc.Tab(label='by Project', value='by-project'),
    dcc.Tab(label='by Month', value='by-month')
])

tab_content = html.Div(id='tab-content')

tabs = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(label='by Person', tab_id='by-person'),
                dbc.Tab(label='by Project', tab_id='by-project'),
                # dbc.Tab(label='by Month', tab_id='by-month'),
            ],
            id='tabs',
            active_tab='by-person',
        ),
        html.Div(id='tabs-content'), 
    ]    
)

table_filter = dcc.Dropdown(
    id='table-filter',
    placeholder='Select a Person',
    persistence=False,
    multi=False,
    style={'margin-top': 10, 'margin-bottom': 10}
)

semester_filter = dcc.Dropdown(
    id='semester-filter',
    placeholder='Select a Semester',
    persistence=False,
    multi=False,
    style={'margin-top': 10, 'margin-bottom': 10}
)


allocation_table = dash_table.DataTable(
        id='allocation-table',
        columns=[{'name': 'Name', 'id': 'Name', 'editable': False, 'deletable': False, 'renamable': False},
                 {'name': 'Project A', 'id': 'Project A', 'deletable': False, 'renamable': False},
                 {'name': 'Project B', 'id': 'Project B', 'deletable': False, 'renamable': False}],
        editable=True,
        row_deletable=False,
        sort_action="native",
        sort_mode="single",
        filter_action="native",
        page_action='none',
        style_table={'overflowY': 'auto', 'overflowX': 'scroll'},
        style_cell={'textAlign': 'center', 'maxWidth': '100px'},
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'right'
            } for c in ['Name']
        ]
    )

filters = dbc.Row(
                [
                    dbc.Col(table_filter, width=6,
                             id='hide-table-filter'),
                    dbc.Col(width=6, id='placeholder-table-filter'),
                    dbc.Col(semester_filter, width=6)
                ]
            )

allocation_div = html.Div(id='allocation-div')

add = dbc.Button(children="Add Project", color='success', size='md', 
                 outline=True, className='mr-1', style={'border-radius': '3px'})
save = dbc.Button(id='save-plan', children="Save Changes", color='success', size='md', className='mr-1',
                  style={'border-radius': '3px'})
clear = dbc.Button("Reset", color='danger', outline=True, size='sm', 
                   className='mr-1', style={'border-radius': '3px'})
export = dbc.Button("Export", color='secondary', size='sm', className='mr-1',
                    style={'border-radius': '3px'})

# Allocation Layout
allocation_layout = html.Div([
    navbar,
    dbc.Container(tabs),
    dbc.Container(filters),
    dbc.Container(allocation_div),
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col([add, save]),
                    dbc.Col(
                        [
                            clear, export
                        ],  style={'text-align': 'right'}
                    )
                ], style={'margin-top': 10}
            )
        ]
    ),
    dcc.Store(id='data-store')
])
