# Erie Bike Cooperative Logging System
# This program records visitor and volunteer information.
# Volunteers have their time and volunteer reason collected to assist with obtaining grants and such.

# Hours of visitors are not recorded


# ------------------ imports -------------------------------------------------------------------------------------------


import fcntl
import socket
import struct

from datetime import datetime
from wtforms.validators import Optional
from werkzeug.security import check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from user import User
from config import DEBUG_HOST, DEBUG_PORT, DATETIME_FORMAT, FLASK_SECRET_KEY
from database import get_db, get_db_readonly, get_saved_volunteers, get_today_volunteers, get_visitors, get_sign_out_list, get_volunteers, get_dates_with_logs
from forms import VisitorForm, VolunteerSignInForm, AdminLogInForm, VolunteerSignOutForm, VolunteerAddForm, DateSelectForm


# ------------------ flask config --------------------------------------------------------------------------------------


# flask app instance
app = Flask(__name__)

# allow nginx proxy to forward data correctly
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=0, x_port=0, x_prefix=0)

# configure secret key for forms
app.config["SECRET_KEY"] = FLASK_SECRET_KEY

# not doing anything at the moment
login_manager = LoginManager(app)

# page to log in
login_manager.login_view = "admin"

# custom login manager error
login_manager.login_message = "Please log in."
login_manager.login_message_category = "error"


# ------------------ user routes ---------------------------------------------------------------------------------------


# home page to select visitor or volunteer with admin panel link in top right corner
@app.get("/")
def greeter():
    # checks
    if current_user.is_authenticated:
        logout_user()

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
        with get_db() as (con, cur):
            statement = f"""
                INSERT INTO visitor_log (datetime, name, reason, email, note)
                VALUES (?, ?, ?, ?, ?)
            """
            parameters = (
                timestamp,
                form.name.data.strip(),
                form.reason.data,
                form.email.data.strip() if form.email.data.strip() else None,
                form.note.data.strip() if form.note.data.strip() else None
            )
            cur.execute(statement, parameters)

        # show success notice on main page
        flash(message=f"Thanks for visiting, {form.name.data}!")
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
    # form
    form = VolunteerSignInForm()

    # data
    volunteer_numbers, names = get_saved_volunteers()
    volunteer_pairs = []

    if len(volunteer_numbers) == 0:
        volunteer_pairs.append("No saved volunteers.")

    for i in range(len(volunteer_numbers)):
        # index 0 has numbers, index 1 has names
        try:
            # try to slice out name with last initial: Johnny A
            space = names[i].index(" ")
            abbr_name = names[i][:space + 2]

            volunteer_pairs.append(f"{volunteer_numbers[i]} - {abbr_name}")
        except ValueError:
            volunteer_pairs.append(f"{volunteer_numbers[i]} - {names[i]}")

    # POST
    if request.method == "POST":
        # don't validate reason if unnecessary
        if request.method == "POST" and request.form.get("number", "").strip():
            form.reason.validators = [Optional()]

    if form.validate_on_submit():
        # get submission timestamp
        now = datetime.now()
        timestamp = now.strftime(DATETIME_FORMAT)

        # check if the user is a regular volunteer
        if form.number.data:
            if form.number.data not in volunteer_numbers:
                # turn volunteer number field red
                form.name.render_kw = {"autofocus": False}
                form.number.render_kw = {"autofocus": True}

                flash("Invalid volunteer number, please ask to be given a number if you volunteer frequently.")
                return render_template("volunteer_form.html", form=form, volunteer_pairs=sorted(volunteer_pairs))
            # valid volunteer number
            else:
                with get_db() as (con, cur):
                    query = f"SELECT name, reason, email FROM volunteers WHERE volunteer_number = ?"
                    cur.execute(query, [form.number.data])
                    data = cur.fetchone()

                    # duplicate prevention
                    today_names, today_hours = get_today_volunteers()

                    if data["name"] in today_names:
                        index = today_names.index(data["name"])
                        if today_hours[index] == 0:
                            flash(f"You are already signed in, {data["name"]}.")
                            return render_template("volunteer_form.html", form=form, volunteer_pairs=sorted(volunteer_pairs))

                    statement = f"INSERT INTO volunteer_log (datetime, name, reason, email, hours) VALUES (?, ?, ?, ?, ?)"
                    parameters = (timestamp, data["name"], data["reason"], data["email"], 0.0)
                    cur.execute(statement, parameters)

                    flash(f"Welcome, {data['name']}! Remember to sign out before leaving.")
                    return redirect(url_for("greeter"))
        # normal form submission
        if not (form.name.data or "").strip():
            # just whitespace for name
            form.name.render_kw = {"autofocus": False}

            flash("Please enter your name and select a reason for volunteering.")
            return render_template("volunteer_form.html", form=form, volunteer_pairs=sorted(volunteer_pairs))

        # duplicate prevention
        today_names, today_hours = get_today_volunteers()

        print(form.name.data)
        print(today_names)

        if form.name.data in today_names:
            index = today_names.index(form.name.data)
            print(today_hours[index])
            if today_hours[index] == 0:
                flash(f"You are already signed in, {form.name.data}.")
                return render_template("volunteer_form.html", form=form, volunteer_pairs=sorted(volunteer_pairs))

        # good submission
        with get_db() as (con, cur):
            statement = f"INSERT INTO volunteer_log (datetime, name, reason, email, note, hours) VALUES (?, ?, ?, ?, ?, ?)"
            parameters = (
                timestamp,
                form.name.data.strip(),
                form.reason.data,
                form.email.data.strip() if form.email.data.strip() else None,
                form.note.data.strip() if form.note.data.strip() else None,
                0.0
            )
            cur.execute(statement, parameters)

            flash(f"Hi, {form.name.data}! Remember to sign out before leaving.")
            return redirect(url_for("greeter"))

    # GET
    return render_template("volunteer_form.html", form=form, volunteer_pairs=sorted(volunteer_pairs))


# volunteer sign out page
@app.route("/volunteer/sign_out", methods=["GET", "POST"])
def volunteer_sign_out():
    # form
    form = VolunteerSignOutForm()

    # data
    volunteers = get_sign_out_list()
    if len(volunteers) == 0:
        flash("There is no one to sign out.")
        return redirect(url_for("volunteer"))
    form.names.choices = [(person["name"], person["name"]) for person in volunteers]

    # POST
    if form.validate_on_submit():
        selected_names = form.names.data

        if len(selected_names) == 0:
            flash("No one was signed out.")
            return redirect(url_for("greeter"))

        with get_db() as (con, cur):
            for person in volunteers:
                if person["name"] in selected_names:
                    statement = "UPDATE volunteer_log SET hours = ? WHERE id = ?"
                    parameters = (round(person["hours"] + 0.01, 2), person["id"])
                    cur.execute(statement, parameters)

        names_string = ", ".join(selected_names)
        flash(f"{names_string} {"has" if len(selected_names) == 1 else "have"} been signed out.")
        return redirect(url_for("greeter"))

    # GET
    return render_template("volunteer_sign_out.html", form=form, volunteers=volunteers)


# ------------------ admin routes --------------------------------------------------------------------------------------


# admin sign in page
@app.route("/admin", methods=["GET", "POST"])
def admin():
    # form
    form = AdminLogInForm()

    # POST
    if form.validate_on_submit():
        with get_db_readonly() as (con, cur):
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


# daily recap of data   -- please fix this shit my god
@app.get("/admin/daily_recap")
@login_required
def daily_recap():
    # data
    visitors = get_visitors()
    num_visitors = len(visitors)
    num_repairs = 0

    for person in visitors:
        if person["reason"] == "Repair":
            num_repairs += 1

    volunteers = get_volunteers()
    num_volunteers = len(volunteers)
    volunteer_hours = 0
    remaining = 0

    for person in volunteers:
        volunteer_hours += person["hours"]
        if person["hours"] == 0:
            remaining += 1

    data = {
        "Visitors today": num_visitors,
        "Visitor repairs": num_repairs,
        "Volunteers today": num_volunteers,
        "Volunteer hours": round(volunteer_hours, 2)
    }

    # GET
    return render_template("daily_recap.html", data=data, remaining=remaining)


# view old data
@app.route("/admin/view_data", methods=["GET", "POST"])
@login_required
def view_data():
    # form
    form = DateSelectForm()

    # data
    dates = get_dates_with_logs()
    form.dates.choices = [(date, date) for date in dates]

    # POST
    if form.validate_on_submit():
        # overwrite dates if we don't want all
        if form.selected.data:
            dates = form.dates.data

        data = []

        for date in dates:
            visitors = get_visitors([date])
            num_visitors = len(visitors)
            num_repairs = 0

            for person in visitors:
                if person["reason"] == "Repair":
                    num_repairs += 1

            volunteers = get_volunteers([date])
            num_volunteers = len(volunteers)
            volunteer_hours = 0

            for person in volunteers:
                volunteer_hours += person["hours"]

            data.append({
                "Date": date,
                "Visitors": num_visitors,
                "Visitor repairs": num_repairs,
                "Volunteers": num_volunteers,
                "Volunteer hours": round(volunteer_hours, 2)
            })

        return render_template("view_data.html", data=data)

    # GET
    return render_template("date_select.html", form=form)


# add regular volunteer form
@app.route("/admin/volunteer/add", methods=["GET", "POST"])
@login_required
def volunteer_add():
    # form
    form = VolunteerAddForm()

    # data
    volunteer_numbers, names = get_saved_volunteers()
    volunteer_pairs = []

    if len(volunteer_numbers) == 0:
        volunteer_pairs.append("No saved volunteers.")

    for i in range(len(volunteer_numbers)):
        # index 0 has numbers, index 1 has names
        try:
            # try to slice out name with last initial: Johnny A
            space = names[i].index(" ")
            abbr_name = names[i][:space + 2]

            volunteer_pairs.append(f"{volunteer_numbers[i]} - {abbr_name}")
        except ValueError:
            volunteer_pairs.append(f"{volunteer_numbers[i]} - {names[i]}")

    # POST
    if form.validate_on_submit():
        if form.number.data in volunteer_numbers:
            flash("Someone is already using that number, pick another one.")
            return render_template("volunteer_add.html", form=form, volunteer_pairs=sorted(volunteer_pairs))

        if form.name.data in names:
            flash(f"{form.name.data}, you already have a number.")
            return render_template("volunteer_add.html", form=form, volunteer_pairs=sorted(volunteer_pairs))

        with get_db() as (con, cur):
            statement = f"INSERT INTO volunteers (volunteer_number, name, reason, email, phone, note) VALUES (?, ?, ?, ?, ?, ?)"
            parameters = (
                form.number.data,
                form.name.data.strip(),
                form.reason.data,
                form.email.data.strip() if form.email.data.strip() else None,
                form.phone.data.strip() if form.phone.data.strip() else None,
                form.note.data.strip() if form.note.data.strip() else None
            )
            cur.execute(statement, parameters)
            flash(f"Volunteer number {form.number.data} has been assigned to {form.name.data}.")
            return redirect(url_for("admin_panel"))

    # GET
    return render_template("volunteer_add.html", form=form, volunteer_pairs=sorted(volunteer_pairs))


# ------------------ API routes ----------------------------------------------------------------------------------------


# return the local network address of the server
@app.get("/api/addr")
def return_addr():
    # debian trixie ethernet default name
    interface = "eno1"

    # create a socket so OS must provide file descriptor
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # kernel sys call to get network address
    address = socket.inet_ntoa(
        fcntl.ioctl(
            s.fileno(),
            0x8915,
            struct.pack('256s', interface[:15].encode('utf-8')))
        [20:24])

    # clean up socket
    s.close()

    reply = {"address": address}
    return jsonify(reply), 200


# ------------------ helper functions ----------------------------------------------------------------------------------


# admin data loader
@login_manager.user_loader
def load_user(user_id: int = 1):
    # pull admin user from database
    with get_db_readonly() as (con, cur):
        cur.execute("SELECT username, password FROM users WHERE id = ?", [user_id])
        user = cur.fetchone()

    return User(user_id=1, username=user["username"], hashed_password=user["password"])


# ------------------ execution guard -----------------------------------------------------------------------------------


# debug server when invoked directly
if __name__ == "__main__":
    app.run(host=DEBUG_HOST, port=DEBUG_PORT, debug=True)
