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

### DIV STORES ###
hours_report = html.Div(id='hours-report', style={'display': 'none'})

fire_me = html.Div(id='fire', children=[], style={'display': 'none'})

### VALID THRU
valid_thru = dbc.Container(html.Div(id='valid-thru'),
                           style={'fontFamily': 'Gill Sans MT, Arial',
                                  'fontSize': 16,
                                  'textAlign': 'left'})

### NAV BAR ###
# Nav Bar
LOGO = app.get_asset_url('ei-logo-white.png')

# nav item links
nav_items = dbc.Container([
    dbc.NavItem(dbc.NavLink('My Utilization', href='/')),
    dbc.NavItem(dbc.NavLink('My Projects', href='/my_projects'))
]
)

# navbar with logo
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=LOGO, height="30px")),
                        dbc.Col(dbc.NavbarBrand("Utilization Report", className="ml-2")),
                    ],
                    align="center",
                    no_gutters=True,
                ),
                # href="/",
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [nav_items], className="ml-auto", navbar=True
                ),
                id="navbar-collapse",
                navbar=True
            ),
        ]
    ),
    color="primary",
    dark=True,
    className="mb-5"
)

### DROPDOWN ###
select_org = dcc.Dropdown(
    id='select-org',
    placeholder='Select one or more teams',
    multi=True
)

select_name = dcc.Dropdown(
    id='select-name',
    placeholder='Begin typing to find your name',
    persistence=True,
    multi=False
)

### UTILIZATION CHART ###
util_card = dbc.Card(
    dcc.Loading(
        dbc.CardBody(
            [
                dcc.Graph(id='utilization-chart',
                          config={'displayModeBar': False}
                          )
            ]
        )
    )
)

# overwrite card for initial deploy
util_card = dcc.Graph(id='utilization-chart',
                          config={'displayModeBar': 'hover',
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

### INSTRUCTIONS ###
instruction_text = dcc.Markdown(
    """
    Utilization is an important measure of the amount of time we spend 
    towards billable projects. Hitting your utilization target helps 
    ensure our company is sustainable.
    
    Utilization is calculated as the number of billable hours divided 
    by the workable hours in the month, regardless of your status as 
    full-time or part-time or the total number of hours you worked.
    
    **Use the slider below to input your expected utilization for the 
    remaining months in this strategic year. Or, return the slider to 'Off' 
    (0%) to use this month's utilization to date to predict utilization.**
    """
)

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

### WEEKLY BAN ###
week_card = dbc.Card(
    [
        dbc.CardHeader("Weekly Summary"),
        dbc.CardBody(
            [
                html.P("Coming Soon!")
            ]
        )
    ], className='w-100 mb-3'
)

### MONTHLY BURN RATE ###
month_card = dbc.Card(
    [
        dbc.CardHeader("Monthly Burn Rate Check"),
        dbc.CardBody(
            [
                html.P("Coming Soon!")
            ]
        )
    ], className='w-100'
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

### DROP DOWN ROW ###
drop_downs = dbc.Container(
    [
        dbc.Row(
            [dbc.Col(select_org, sm=12, md=6),
             dbc.Col(select_name, sm=12, md=6)]
        )
    ]
)

drop_downs = dbc.Container(
    select_name
)

# Reset Chart
reset_chart = dbc.Button("Reset", id='reset-axes',
            color='secondary', 
            outline=True, size='sm')

### TOP ROW ###
utilization_display = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(util_card, width=8),
                dbc.Col(
                    [
                        dbc.Row(week_card, className='h-50'),
                        dbc.Row(month_card, className='h-50')
                    ], width=4
                )
            ]
        )
    ],
    style={"height": "100vh"}
)

utilization_display = dbc.Row(
            [
                dbc.Col(util_card, md=7, sm=10),
                dbc.Col(util_slider, md=1, sm=2),
                dbc.Col(
                    [
                        dbc.Row(dbc.Col(week_card, className='h-50')),
                        dbc.Row(dbc.Col(month_card, className='h-50'))
                    ], md=3, sm=10
                )
            ], justify='center', align='center'
        )

utilization_display = dbc.Row(
            [
                dbc.Col(util_card, md=7, sm=10),
                dbc.Col(util_slider, md=1, sm=2),
                dbc.Col(
                    [
                        dbc.Row(dbc.Col(instructions))
                    ], md=3, sm=10
                )
            ], justify='center', align='center'
        )

utilization_display = dbc.Row(
            [
                dbc.Col(util_card, md=11, sm=11),
                dbc.Col(util_slider, md=1, sm=1)
            ], justify='center', align='center'
        )

# Main Layout
layout_main = html.Div([
    navbar,
    dbc.Container(instruction_text),
    drop_downs,
    html.Br(),
    dbc.Container(reset_chart),
    dbc.Container(utilization_display),
    html.Br(),
    valid_thru,
    html.Br(),
    fire_me
])


### My Projects Layout ###
### INSTRUCTIONS ###
instruction_text = [
    "Explore the projects and tasks you've been working on.",
    html.Br(), html.Br(),
    html.B("Use the date selector to filter by date. "
           "Click in the bar chart to see tasks related to each project. "
           "Review time entries and comments in the table below. "
           "Click 'Reset' to start over."),
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
                updatemode='bothdates',
                style={'borderWidth': 0}  
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
reset_chart = dbc.Button("Reset", id='clear-clickData',
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

### LAYOUT ###
projects_layout = html.Div([
    navbar,
    dbc.Container(instruction_text),
    user_input,
    html.Br(),
    dbc.Container(reset_chart),
    dcc.Loading(dbc.Container(projects_graph)),
    html.Br(),
    entry_table,
    html.Br(), html.Br(),
    valid_thru,
    html.Br(),
    fire_me
])


allocation_table = dash_table.DataTable(
        id='allocation-table',
        columns=[{'name': 'Name', 'id': 'Name', 'editable': False, 'deletable': False, 'renamable': False},
                 {'name': 'Project A', 'id': 'Project A', 'deletable': False, 'renamable': False},
                 {'name': 'Project B', 'id': 'Project B', 'deletable': False, 'renamable': False}],
        data=[{'Name': 'Erik', 'Project A': .5, 'Project B': .5},
              {'Name': 'Kristen', 'Project A': .5, 'Project B': .5}],
        editable=True,
        row_deletable=False,
        sort_action="native",
        sort_mode="single",
        filter_action="native",
        page_action='none',
        style_table={'overflowY': 'auto'},
        style_cell={'textAlign': 'center', 'maxWidth': '100px'},
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'right'
            } for c in ['Name']
        ]
    )

# Allocation Layout
allocation_layout = html.Div([
    navbar,
    allocation_table
])


if __name__ == '__main__':
    app.run_server(debug=True)