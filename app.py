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
app.server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DO NOT PUT CARRIAGE RETURNS IN CONNECTION STRING !!!
# db connection for local, REPLACE PASSWORD BUT DON'T COMMIT
# app.server.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:Sup249249*@localhost/test"

# db connection for heroku 
app.server.config["SQLALCHEMY_DATABASE_URI"] = "postgres://lnjlwhszyveeql:54058548e3aef6f075340d5a41d21dd517008adfbf0b12a44e3ce19e18d596a4@ec2-54-204-26-236.compute-1.amazonaws.com:5432/d7hkmgh5gmk0b4"

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
