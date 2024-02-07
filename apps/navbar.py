from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

from app import app

LOGO = app.get_asset_url('ei-logo-white.png')

### NAVBAR ###
nav_items = dbc.Nav([
    dbc.NavItem(dbc.NavLink('My Utilization', href='/')),
    dbc.NavItem(dbc.NavLink('My Projects', href='/my_projects')),
    dbc.NavItem(dbc.NavLink('My Team', href='/my_team')),
    dbc.NavItem(dbc.NavLink('Projections', href='/my_forecast')),
    ],
    className='ms-auto'
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=LOGO, height="30px")),
                        dbc.Col(dbc.NavbarBrand("Utilization Report", className="ms-2")),
                    ],
                    align="center",
                ),
                # href="/",
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                    children=[nav_items],
                    id="navbar-collapse",
                    is_open=False,
                    navbar=True,
                ),
        ],
    ),
    color="primary",
    dark=True,
)


### ---------------------------- CALLBACKS ------------------------------- ###
# add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
