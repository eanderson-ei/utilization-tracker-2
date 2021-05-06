import dash_html_components as html
import dash_bootstrap_components as dbc

from app import app

LOGO = app.get_asset_url('ei-logo-white.png')

### ----------------------------- LAYOUT ----------------------------------###

### NAVBAR ###
nav_items = dbc.Container([
    dbc.NavItem(dbc.NavLink('My Utilization', href='/')),
    dbc.NavItem(dbc.NavLink('My Projects', href='/my_projects')),
    # dbc.NavItem(dbc.NavLink('Allocation', href='/allocation'))  # turn on for dev
]
)

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