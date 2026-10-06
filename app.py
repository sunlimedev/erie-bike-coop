



# ------------------ imports -------------------------------------------------------------------------------------------


import csv

from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request
from flask_login import LoginManager, UserMixin

from forms import SignInForm


# ------------------ constants -----------------------------------------------------------------------------------------


# location to store csv files
CSV_PATH = Path("logs")
CSV_PATH.mkdir(parents=True, exist_ok=True)


# ------------------ flask config --------------------------------------------------------------------------------------


app = Flask(__name__)

app.config['SECRET_KEY'] = 'awsdkfhjdgbkajsuhdvfkjhvasdkjfvaksdjvf'

login_manager = LoginManager(app)


# ------------------ classes -------------------------------------------------------------------------------------------


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
        today = now.strftime("%Y-%m-%d")
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        file_path = CSV_PATH / f"{today}.csv"

        headers = ["Date", "Name", "Type", "Reason", "Email", "Phone", "Hours"]

        reason = ""

        if not file_path.is_file():
            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(headers)

        if form.type.data == "visitor":
            if not form.visitor_reason.data:
                reason = ""
            else:
                reason = form.visitor_reason.data
        if form.type.data == "volunteer":
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


@login_manager.user_loader
def load_user():
    return User("a", "a", "a")


# ------------------ execution guard -----------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(debug=True)