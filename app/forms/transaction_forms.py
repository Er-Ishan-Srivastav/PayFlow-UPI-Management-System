from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange, Length, Optional


class SendMoneyForm(FlaskForm):
    receiver_upi = StringField("Receiver UPI ID", validators=[DataRequired(), Length(max=50)])
    amount = DecimalField(
        "Amount", validators=[DataRequired(), NumberRange(min=1, max=100000)], places=2
    )
    remarks = TextAreaField("Remarks", validators=[Optional(), Length(max=100)])
    pin = PasswordField("UPI PIN", validators=[DataRequired(), Length(min=4, max=6)])
    submit = SubmitField("Pay now")


class BeneficiaryForm(FlaskForm):
    ben_name = StringField("Name", validators=[DataRequired(), Length(max=50)])
    ben_upi = StringField("UPI ID", validators=[DataRequired(), Length(max=50)])
    submit = SubmitField("Save beneficiary")


class HistoryFilterForm(FlaskForm):
    q = StringField("Search", validators=[Optional(), Length(max=80)])
    status = SelectField(
        "Status",
        choices=[("", "All statuses"), ("SUCCESS", "Success"), ("FAILED", "Failed"), ("PENDING", "Pending")],
        default="",
    )
    direction = SelectField(
        "Direction",
        choices=[("", "Sent & received"), ("sent", "Sent"), ("received", "Received")],
        default="",
    )
