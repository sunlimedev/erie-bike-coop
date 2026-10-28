# Import file


from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Optional
from wtforms.widgets.core import CheckboxInput, ListWidget
from wtforms.fields import StringField, EmailField, RadioField, SubmitField, IntegerField, PasswordField, SelectMultipleField


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
            ("Repair", "Repairing a bike"),
            ("Earn-a-Bike", "Earn-a-Bike session"),
            ("Info", "Getting info / Just curious"),
            ("Purchase bike or parts", "Purchasing bike or parts"),
            ("Donate bike or parts", "Donating bike or parts"),
            ("Donate money", "Donating money")
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


class VolunteerSignInForm(FlaskForm):
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
            ("Help", "Here to help"),
            ("Center", "I'm from the Center"),
            ("Service", "Service hours"),
            ("Other", "Other")
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


class VolunteerSignOutForm(FlaskForm):
    names = SelectMultipleField(
        label="Current Volunteers",
        choices=[],
        option_widget=CheckboxInput(),
        widget=ListWidget(prefix_label=False)  # type: ignore
    )
    submit = SubmitField(
        label="Sign out"
    )


class AdminLogInForm(FlaskForm):
    password = PasswordField(
        label="Admin Password",
        validators=[InputRequired(message="Please enter your password.")],
        render_kw={"autofocus": True}
    )
    submit = SubmitField(
        label="Log in"
    )
