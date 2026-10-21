# Erie Bike Cooperative Sign In Form System

# This program records visitor and volunteer information.
# Volunteers have their time and volunteer reason collected to assist with grants and such.
# A backup program aggregates the daily .csv files into monthly tables and emails them to a specific address.


# ------------------ imports -------------------------------------------------------------------------------------------


import os
import csv

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin

from forms import VisitorForm, VolunteerForm


# ------------------ constants -----------------------------------------------------------------------------------------


load_dotenv()

# host and port for debug server
HOST = "0.0.0.0"
PORT = 8080

# directory for csv files
FORM_DATA_FOLDER = "logs"


# ------------------ flask config --------------------------------------------------------------------------------------


app = Flask(__name__)

# configure secret key for forms
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "abcdefghijklmnopqrstuvwxyz")

# not doing anything at the moment
login_manager = LoginManager(app)


# ------------------ classes -------------------------------------------------------------------------------------------


# not currently used but here for the future
class User(UserMixin):
    def __init__(self, user_id, username, hashed_password):
        self.id = user_id
        self.username = username
        self.hashed_password = hashed_password


# ------------------ routes --------------------------------------------------------------------------------------------


@app.get("/")
def greeter():
    return render_template("greeter.html")


@app.route("/visitor_form", methods=["GET", "POST"])
def visitor_form():
    # form
    form = VisitorForm()

    # GET
    return render_template("visitor_form.html", form=form)


@app.route("/volunteer_form", methods=["GET", "POST"])
def volunteer_form():
    # form
    form = VolunteerForm()

    # GET
    return render_template("volunteer_form.html", form=form)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    # GET
    return render_template("admin.html")


@app.route("/sign_out", methods=["GET", "POST"])
def sign_out():
    # GET
    return render_template("sign_out.html")


# ------------------ helper functions ----------------------------------------------------------------------------------


# glue code to make the server not freak out
@login_manager.user_loader
def load_user():
    return User("a", "a", "a")


# ------------------ execution guard -----------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
