


# ------------------ imports -------------------------------------------------------------------------------------------


import csv

from pathlib import Path
from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager, UserMixin

from forms import SignInForm
from data import backup


# ------------------ constants -----------------------------------------------------------------------------------------





# ------------------ flask config --------------------------------------------------------------------------------------


app = Flask(__name__)

app.config['SECRET_KEY'] = 'bicycle'

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
    # form
    form = SignInForm()

    # POST
    if form.validate_on_submit():
        now = datetime.now()
        year = now.strftime("%Y")
        month_day = now.strftime("%m-%d")
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        # dynamically create csv file for logging
        file_path = Path(f"{year}/{month_day}.csv")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # column names for csv
        columns = ["Date", "Name", "Type", "Reason", "Email", "Phone", "Hours"]

        # creates a new file on a new month or a fresh install
        if not file_path.is_file():
            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(columns)

            backup()

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
                form.phone.data
            ]

            writer.writerow(row)

        return render_template("greeter.html", form=form)

    # GET
    return render_template("greeter.html", form=form)


# ------------------ helper functions ----------------------------------------------------------------------------------


# glue code to make the server not freak out
@login_manager.user_loader
def load_user():
    return User("a", "a", "a")


# ------------------ execution guard -----------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(debug=True)