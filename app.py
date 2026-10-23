# Erie Bike Cooperative Logging System
# This program records visitor and volunteer information.
# Volunteers have their time and volunteer reason collected to assist with obtaining grants and such.


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
from flask_login import LoginManager

from forms import VisitorForm, VolunteerForm, AdminLogInForm
from user import User


# ------------------ constants -----------------------------------------------------------------------------------------


# load environment file into environment variables
load_dotenv()

# host and port for debug server when invoked directly
HOST = "0.0.0.0"
PORT = 8080

# sqlite database file
DATABASE_FILE = Path("app.db")

# admin password
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "pass")


# ------------------ flask config --------------------------------------------------------------------------------------


# flask app instance
app = Flask(__name__)

# configure secret key for forms
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "abcdefghijklmnopqrstuvwxyz")

# not doing anything at the moment
login_manager = LoginManager(app)


# ------------------ user routes ---------------------------------------------------------------------------------------


# home page to select visitor or volunteer with admin panel link in top right corner
@app.get("/")
def greeter():
    # GET
    return render_template("greeter.html")


# visitor form with no hour tracking
@app.route("/visitor/form", methods=["GET", "POST"])
def visitor_form():
    # form
    form = VisitorForm()

    # POST
    if form.validate_on_submit():
        print(form.data)

    # GET
    return render_template("visitor_form.html", form=form)


# volunteer sign in/out select page
@app.route("/volunteer", methods=["GET", "POST"])
def volunteer():
    # GET
    pass


# volunteer form with hour tracking
@app.route("/volunteer/form", methods=["GET", "POST"])
def volunteer_form():
    # form
    form = VolunteerForm()

    # POST
    if form.validate_on_submit():
        print(form.data)

    # GET
    return render_template("volunteer_form.html", form=form)


# volunteer sign out page
@app.route("/volunteer/sign_out", methods=["GET", "POST"])
def sign_out():
    # GET
    return render_template("volunteer_sign_out.html")


# ------------------ admin routes --------------------------------------------------------------------------------------


# admin sign in page
@app.route("/admin", methods=["GET", "POST"])
def admin():
    # form
    form = AdminLogInForm()

    # GET
    return render_template("admin.html", form=form)


# admin panel
@app.get("/admin/panel")
def admin_panel():
    # GET
    return render_template("admin_panel.html")


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


def get_db_tables():
    # list for table names
    tables = []

    with get_db() as (con, cur):
        cur.execute("SELECT * FROM pragma_table_list();")

        for row in cur.fetchall():
            if not row["name"].startswith("sqlite_"):
                tables.append(row["name"])

    return tables


# ------------------ execution guard -----------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
