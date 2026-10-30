# Application Database Functions File


# ------------------ imports -------------------------------------------------------------------------------------------


import sqlite3

from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from werkzeug.security import generate_password_hash

from config import ADMIN_PASSWORD, DATABASE_FILE, DATETIME_FORMAT


# ------------------ functions -----------------------------------------------------------------------------------------


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


# get regular volunteers
def get_volunteers():
    # create lists
    volunteer_numbers = []
    names = []

    with get_db() as (con, cur):
        cur.execute("SELECT volunteer_number, name FROM volunteers;")

        # extract the data
        for row in cur.fetchall():
            volunteer_numbers.append(row["volunteer_number"])
            names.append(row["name"])

    return volunteer_numbers, names


# get today's volunteers with hours
def get_today_volunteers():
    with get_db() as (con, cur):
        query = "SELECT name, hours FROM volunteer_log WHERE date (datetime) = date ('now', 'localtime');"
        cur.execute(query)

        names = []
        hours = []

        for row in cur.fetchall():
            names.append(row["name"])
            hours.append(row["hours"])

    # lists are reversed so most recent entries come first in case there are two valid sessions on the same day
    return list(reversed(names)), list(reversed(hours))


# get today's visitors
def get_today_visitors():
    with get_db() as (con, cur):
        query = "SELECT name, reason FROM visitor_log WHERE date (datetime) = date ('now', 'localtime');"
        cur.execute(query)

        visitors = []

        for row in cur.fetchall():
            visitors.append({
                "name": row["name"],
                "reason": row["reason"]
            })

    return visitors


# generate list for sign out page
def get_sign_out_list():
    with get_db() as (con, cur):
        query = "SELECT id, datetime, name, hours FROM volunteer_log WHERE date (datetime) = date ('now', 'localtime');"
        cur.execute(query)

        volunteers = []

        for row in cur.fetchall():
            if row["hours"] != 0:
                continue

            start = datetime.strptime(row["datetime"], DATETIME_FORMAT)
            end = datetime.now()
            duration = end - start
            hours = round(duration.total_seconds() / 3600, 2)

            volunteers.append({
                "id": row["id"],
                "name": row["name"],
                "hours": hours
            })

    return volunteers
