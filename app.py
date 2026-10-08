# Erie Bike Cooperative Sign In Form System

# This program records visitor and volunteer information.
# Volunteers have their time and volunteer reason collected to assist with grants and such.
# A backup program aggregates the daily .csv files into monthly tables and emails them to a specific address.


# ------------------ imports -------------------------------------------------------------------------------------------


import os
import csv

from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin

from forms import SignInForm, SignOutForm


# ------------------ constants -----------------------------------------------------------------------------------------


# host and port for debug server
HOST = "0.0.0.0"
PORT = 5000

# directory for csv files
FORM_DATA_FOLDER = "logs"

# flask cookie/session key
SECRET_KEY = os.getenv("FLASK_SECRET_KEY")


# ------------------ flask config --------------------------------------------------------------------------------------


app = Flask(__name__)

app.config['SECRET_KEY'] = SECRET_KEY

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


@app.route("/", methods=["GET", "POST"])
@app.route("/greeter", methods=["GET", "POST"])
def greeter():
    return render_template("greeter.html")


@app.route("/sign_in", methods=["GET", "POST"])
def sign_in():
    # form
    form = SignInForm()

    # POST
    if form.validate_on_submit():
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        # dynamically create csv file for logging
        file_path = Path(f"{FORM_DATA_FOLDER}/{today}.csv")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # column names for csv
        columns = ["Date", "Name", "Type", "Reason", "Email", "Phone", "Hours"]

        # creates a new file on a new month or a fresh install
        if not file_path.is_file():
            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(columns)

        # grab the correct reason data if present
        if form.type.data == "visitor":
            if not form.visitor_reason.data:
                reason = ""
            else:
                reason = form.visitor_reason.data
        else:
            if not form.volunteer_reason.data:
                reason = ""
            else:
                reason = form.volunteer_reason.data

        with open(file_path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            row = [
                timestamp,
                form.name.data,
                form.type.data,
                reason,
                form.email.data,
                form.phone.data,
                "0"
            ]

            writer.writerow(row)

        flash(f"Thanks for coming, {form.name.data}!", "success")
        return redirect(url_for("greeter"))

    # GET
    return render_template("sign_in.html", form=form)


@app.route("/sign_out", methods=["GET", "POST"])
def sign_out():
    # checks/data
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_format = "%Y-%m-%d %H:%M:%S"

    file_path = Path(f"{FORM_DATA_FOLDER}/{today}.csv")

    if not file_path.is_file():
        flash("There is no one to sign out.", "notify")
        return redirect(url_for("greeter"))

    try:
        with open(file_path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)

            # skip header row
            headers = next(reader)

            dates = []
            names = []
            types = []
            reasons = []
            emails = []
            phones = []
            hours = []

            volunteers = []

            for row in reader:
                if row[2] == "volunteer" and row[6] == "0":
                    # get hours since volunteer started
                    start_time = datetime.strptime(row[0], timestamp_format)
                    current_time = datetime.strptime(timestamp, timestamp_format)
                    time = round((current_time - start_time).total_seconds() / 3600, ndigits=2)

                    volunteers.append({
                        "name": row[1],
                        "hours": time
                    })

                dates.append(row[0])
                names.append(row[1])
                types.append(row[2])
                reasons.append(row[3])
                emails.append(row[4])
                phones.append(row[5])
                hours.append(row[6])
    except OSError:
        flash("No one has signed in today.", "notify")
        return redirect(url_for("greeter"))

    if len(volunteers) == 0:
        flash("There is no one to sign out.", "notify")
        return redirect(url_for("greeter"))

    # form
    form = SignOutForm()
    form.names.choices = [(volunteer["name"], volunteer["name"]) for volunteer in volunteers]

    # POST
    if form.validate_on_submit():
        selected_names = form.names.data

        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

            # adjust hours of volunteer since they are being signed out
            for i in range(len(names)):
                if names[i] in selected_names:
                    start_time = datetime.strptime(dates[i], timestamp_format)
                    current_time = datetime.strptime(timestamp, timestamp_format)
                    hours[i] = str(round(((current_time - start_time).total_seconds() / 3600) + 0.01, ndigits=2))

                # rebuild the file
                writer.writerow([dates[i], names[i], types[i], reasons[i], emails[i], phones[i], hours[i]])

        # show the volunteers signed out on greeter page
        signed_out_names = ", ".join(selected_names)
        verb = "has" if len(selected_names) == 1 else "have"
        flash(f"{signed_out_names} {verb} been signed out.", "success")
        return redirect(url_for("greeter"))

    # GET
    return render_template("sign_out.html", volunteers=volunteers, form=form)


# ------------------ helper functions ----------------------------------------------------------------------------------


# glue code to make the server not freak out
@login_manager.user_loader
def load_user():
    return User("a", "a", "a")


# ------------------ execution guard -----------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)