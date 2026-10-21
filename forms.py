from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, RadioField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Optional


class VisitorForm(FlaskForm):
    name = StringField(
        label="What is your name?",
        validators=[InputRequired(message="Please enter your name.")],
        render_kw={"autofocus": True}
    )
    reason = RadioField(
        label="What brings you in?",
        validators=[InputRequired(message="Please choose a reason for visiting.")],
        choices=[
            ("repair", "Repairing a bike"),
            ("earn bike", "Earn-a-Bike session"),
            ("info", "Getting info / Just curious"),
            ("purchase bike", "Purchasing bike or parts"),
            ("donate bike", "Donating bike or parts"),
            ("donate money", "Donating money")
        ]
    )
    email = EmailField(
        label="What is your email address?",
        validators=[Optional()],
        render_kw={"placeholder": "optional"}
    )
    note = StringField(
        label="What is your note?",
        validators=[Optional()],
        render_kw={"placeholder": "optional"}
    )
    submit = SubmitField(
        label="Done"
    )


class VolunteerForm(FlaskForm):
    name = StringField(
        label="What is your name?",
        validators=[Optional()],
        render_kw={"autofocus": True}
    )
    number = IntegerField(
        label="Volunteer #",
        validators=[Optional()],
        render_kw={"placeholder": "optional"}
    )
    reason = RadioField(
        label="What brings you in?",
        validators=[InputRequired(message="Please choose a reason for visiting.")],
        choices=[
            ("general service", "General service hours"),
            ("school", "Service hours for school"),
            ("correctional", "I'm from the Center"),
            ("help", "Here to help")
        ]
    )
    email = EmailField(
        label="What is your email address?",
        validators=[Optional()],
        render_kw={"placeholder": "optional"}
    )
    note = StringField(
        label="Note",
        validators=[Optional()],
        render_kw={"placeholder": "optional"}
    )
    submit = SubmitField(
        label="Done"
    )