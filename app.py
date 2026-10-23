# Erie Bike Cooperative Sign In Form System
# This program records visitor and volunteer information.
# Volunteers have their time and volunteer reason collected to assist with grants and such.
# A backup program aggregates the daily .csv files into monthly tables and emails them to a specific address.


# ------------------ imports -------------------------------------------------------------------------------------------


import os
import csv
import sqlite3

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin

from forms import VisitorForm, VolunteerForm


# ------------------ constants -----------------------------------------------------------------------------------------


load_dotenv()

# host and port for debug server
HOST = "0.0.0.0"
PORT = 8080

# sqlite database file
DATABASE_FILE = Path("app.db")

# admin password
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "pass")


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
@app.get("/home")
@app.get("/greeter")
def greeter():
    return render_template("greeter.html")


@app.route("/visitor_form", methods=["GET", "POST"])
def visitor_form():
    # form
    form = VisitorForm()

    # POST
    if form.validate_on_submit():
        print(form.data)

    # GET
    return render_template("visitor_form.html", form=form)


@app.route("/volunteer", methods=["GET", "POST"])
def volunteer():
    # GET
    pass


@app.route("/volunteer_form", methods=["GET", "POST"])
def volunteer_form():
    # form
    form = VolunteerForm()

    # POST
    if form.validate_on_submit():
        print(form.data)

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


# mode string exists to use BEGIN IMMEDIATE transaction mode for immediate write locking when writing
@contextmanager
def get_db(mode: str = "r"):
    # create file if necessary with admin user
    if not DATABASE_FILE.is_file():
        create_db(DATABASE_FILE)

    # connect to database without locking file
    con = sqlite3.connect(DATABASE_FILE, isolation_level=None)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # execute pragmas for better concurrency
    pragmas = [
        "PRAGMA synchronous = NORMAL;",
        "PRAGMA busy_timeout = 5000;",
        "PRAGMA cache_size = -20000;"
    ]
    for pragma in pragmas:
        cur.execute(pragma)

    # lock file if writing
    if mode == "w":
        cur.execute("BEGIN IMMEDIATE")

    # yield the database connection to the caller
    try:
        yield con, cur
        if mode == "w":
            con.commit()
    except Exception:
        if mode == "w":
            con.rollback()
        raise
    finally:
        cur.close()
        con.close()


def create_db(db: Path):
    # create database
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # switch to WAL for better concurrency
    pragmas = [
        "PRAGMA journal_mode = WAL;",
        "PRAGMA synchronous = NORMAL;",
        "PRAGMA busy_timeout = 5000;",
        "PRAGMA cache_size = -20000;"
    ]
    for pragma in pragmas:
        cur.execute(pragma)

    # create user table
    user_table = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
    """
    cur.execute(user_table)

    # add admin account
    admin_query = """
        INSERT INTO users (username, password) 
        VALUES (?, ?);
    """
    admin_credentials = ("admin", generate_password_hash(ADMIN_PASSWORD))
    cur.execute(admin_query, admin_credentials)

    # commit changes and close
    con.commit()
    con.close()


# ------------------ execution guard -----------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
