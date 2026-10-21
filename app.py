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

from forms import SignInForm, SignOutForm


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


@app.route("/visitor", methods=["GET", "POST"])
def visitor():
    # GET
    return render_template("visitor.html")


@app.route("/volunteer", methods=["GET", "POST"])
def volunteer():
    # GET
    return render_template("volunteer.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    # GET
    return render_template("admin.html")


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
