import dash
import dash_bootstrap_components as dbc
import dash_auth
import json
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

external_stylesheets = [dbc.themes.LITERA]  # Also try LITERA, SPACELAB

server = Flask(__name__)
app = dash.Dash(__name__, server=server,
                external_stylesheets=external_stylesheets, 
                show_undo_redo=True)
app.config.suppress_callback_exceptions = True
app.server.config['SQLALCHEM_TRACK_MODIFICATIONS'] = False

# app.server.config["SQLALCHEMY_DATABASE_URI"] = ""

db = SQLAlchemy(app.server)

# Keep this out of source code repository - save in a file or a database
# Local dev
try:
    with open('secrets/passwords.json') as f:
        VALID_USERNAME_PASSWORD_PAIRS = json.load(f)
# Heroku dev
except:
    json_creds = os.environ.get("VALID_USERNAME_PASSWORD_PAIRS")
    VALID_USERNAME_PASSWORD_PAIRS = json.loads(json_creds)

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
