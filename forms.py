from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, RadioField, SubmitField, TelField, SelectMultipleField
from wtforms.validators import InputRequired, Optional
from wtforms.widgets.core import CheckboxInput, ListWidget


class SignInForm(FlaskForm):
    name = StringField(
        label="What is your full name?",
        validators=[
            InputRequired(message="Please enter your name.")
        ]
    )
    type = RadioField(
        label="What brings you in?",
        choices=[
            ("visitor", "I am visiting"),
            ("volunteer", "I am volunteering")
        ],
        validators=[
            InputRequired(message="Please select one of these options:")
        ]
    )
    visitor_reason = RadioField(
        label="What is your reason for visiting?",
        choices=[
            ("repair", "Repairing a bike myself"),
            ("earn bike", "Earn-a-Bike session"),
            ("info", "Getting info / Just curious"),
            ("donate money", "Donating money"),
            ("donate bike", "Donating bike or parts"),
            ("purchase bike", "Purchasing bike or parts")
        ],
        validators=[Optional()]
    )
    volunteer_reason = RadioField(
        label="What is your reason for volunteering?",
        choices=[
            ("school", "Service hours for school"),
            ("correctional", "Service hours for correctional program"),
            ("court", "Service hours for court"),
            ("help", "Just wanted to help")
        ],
        validators=[Optional()]
    )
    email = EmailField(
        label="What is your email address?",
        validators=[Optional()]
    )
    phone = TelField(
        label="What is your phone number?",
        validators=[Optional()]
    )
    submit = SubmitField(
        label="Sign in"
    )


class SignOutForm(FlaskForm):
    names = SelectMultipleField(
        label="Current Volunteers",
        choices=[],
        option_widget=CheckboxInput(),
        widget=ListWidget(prefix_label=False) # type: ignore
    )
    submit = SubmitField(
        label="Sign out"
    )