# Erie Bike Cooperative Logging System
# This program records visitor and volunteer information.
# Volunteers have their time and volunteer reason collected to assist with obtaining grants and such.

# Hours of visitors are not recorded


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
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

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
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")

# ISO8601 datetime format for application
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


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
        # get submission timestamp
        now = datetime.now()
        timestamp = now.strftime(DATETIME_FORMAT)

        # insert the new data into the database and insert None for empty strings
        with get_db("w") as (con, cur):
            statement = f"""
                INSERT INTO visitor_log (datetime, name, reason, email, note)
                VALUES (?, ?, ?, ?, ?)
            """
            parameters = (
                timestamp,
                form.name.data,
                form.reason.data,
                form.email.data if form.email.data.strip() else None,
                form.note.data if form.note.data.strip() else None
            )
            cur.execute(statement, parameters)

        # show success notice on main page
        flash(message=f"Thanks for visiting, {form.name.data}!", category="success")
        return redirect(url_for("greeter"))

    # GET
    return render_template("visitor_form.html", form=form)


# volunteer sign in/out select page
@app.get("/volunteer")
def volunteer():
    # GET
    return render_template("volunteer.html")


# volunteer form with hour tracking
@app.route("/volunteer/form", methods=["GET", "POST"])
def volunteer_form():


    # NOT DONE

    # form
    form = VolunteerForm()

    # POST
    if form.validate_on_submit():
        # get submission timestamp
        now = datetime.now()
        timestamp = now.strftime(DATETIME_FORMAT)

        # insert the new data into the database and insert None for empty strings
        with get_db("w") as (con, cur):

            # insert the new data into the database and insert None for empty strings
            statement = f"""
                INSERT INTO volunteer_log (datetime, name, reason, email, note, hours)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            parameters = (
                timestamp,
                form.name.data,
                form.reason.data,
                form.email.data if form.email.data.strip() else None,
                form.note.data if form.note.data.strip() else None,
                0.0
            )
            cur.execute(statement, parameters)

        # show success notice on main page
        flash(message=f"Thanks for volunteering, {form.name.data}! Remember to sign out before you leave.", category="success")
        return redirect(url_for("greeter"))

    # GET
    return render_template("volunteer_form.html", form=form, volunteers=["a"])


# volunteer sign out page
@app.route("/volunteer/sign_out", methods=["GET", "POST"])
def volunteer_sign_out():
    # GET
    return render_template("volunteer_sign_out.html")


# ------------------ admin routes --------------------------------------------------------------------------------------


# admin sign in page
@app.route("/admin", methods=["GET", "POST"])
def admin():
    # form
    form = AdminLogInForm()

    # POST
    if form.validate_on_submit():
        with get_db() as (con, cur):
            cur.execute("SELECT password FROM users WHERE id = 1")
            row = cur.fetchone()

            if check_password_hash(pwhash=row["password"], password=form.password.data):
                user = load_user()
                login_user(user)
                return redirect(url_for("admin_panel"))
            else:
                return render_template("admin.html", form=form)

    # GET
    return render_template("admin.html", form=form)


# admin panel
@app.get("/admin/panel")
@login_required
def admin_panel():
    # GET
    return render_template("admin_panel.html")


# ------------------ helper functions ----------------------------------------------------------------------------------


# admin data loader
@login_manager.user_loader
def load_user(user_id: int = 1):
    # pull admin user from database
    with get_db() as (con, cur):
        cur.execute("SELECT username, password FROM users WHERE id = ?", [user_id])
        user = cur.fetchone()

    return User(user_id=1, username=user["username"], hashed_password=user["password"])


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


# create the sqlite file with admin user
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
    admin_statement = """
        INSERT INTO users (username, password) 
        VALUES (?, ?);
    """
    admin_credentials = ("admin", generate_password_hash(ADMIN_PASSWORD))
    cur.execute(admin_statement, admin_credentials)

    # create volunteers table
    volunteers_statement = f"""
        CREATE TABLE volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            volunteer_number INTEGER NOT NULL,
            name TEXT NOT NULL,
            reason TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            note TEXT
        );
    """
    cur.execute(volunteers_statement)

    # create visitor log table
    visitor_log_statement = f"""
        CREATE TABLE visitor_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            name TEXT NOT NULL,
            reason TEXT NOT NULL,
            email TEXT,
            note TEXT
        );
    """
    cur.execute(visitor_log_statement)

    # create volunteer log table
    volunteer_log_statement = f"""
        CREATE TABLE volunteer_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            name TEXT NOT NULL,
            reason TEXT NOT NULL,
            email TEXT,
            note TEXT,
            hours REAL NOT NULL
        );
    """
    cur.execute(volunteer_log_statement)

    # commit changes and close
    con.commit()
    cur.close()
    con.close()


# get table names in database
def get_db_tables():
    # create table list
    tables = []

    with get_db() as (con, cur):
        cur.execute("SELECT * FROM pragma_table_list();")

        # extract the custom tables
        for row in cur.fetchall():
            if not row["name"].startswith("sqlite_"):
                tables.append(row["name"])

    return tables


# ------------------ execution guard -----------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
