import dash
import dash_bootstrap_components as dbc
import dash_auth
import json
import os
from flask import Flask
# from flask_sqlalchemy import SQLAlchemy

print("starting app.py")

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
# try:
#     app.server.config["SQLALCHEMY_DATABASE_URI"] = os.environ['DATABASE_URL']
#     app.server.debug = False
# except:
#     with open ('secrets/database_uri.json') as f:
#         app.server.config["SQLALCHEMY_DATABASE_URI"] = json.load(f).get("DATABASE_URI")
#     app.server.debug = True
    
# db = SQLAlchemy(app.server)


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

print("ran app.py")
