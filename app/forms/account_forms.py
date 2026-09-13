from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField, DecimalField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, Regexp


class LinkBankForm(FlaskForm):
    bank_name = SelectField(
        "Bank",
        choices=[
            ("State Bank of India", "State Bank of India"),
            ("HDFC Bank", "HDFC Bank"),
            ("ICICI Bank", "ICICI Bank"),
            ("Axis Bank", "Axis Bank"),
            ("Kotak Mahindra Bank", "Kotak Mahindra Bank"),
            ("Punjab National Bank", "Punjab National Bank"),
            ("Yes Bank", "Yes Bank"),
        ],
        validators=[DataRequired()],
    )
    account_no = StringField(
        "Account number", validators=[DataRequired(), Length(min=8, max=20), Regexp(r"^[0-9]+$")]
    )
    ifsc_code = StringField(
        "IFSC code",
        validators=[DataRequired(), Length(min=11, max=11), Regexp(r"^[A-Z]{4}0[A-Z0-9]{6}$")],
    )
    account_type = SelectField(
        "Account type",
        choices=[("Savings", "Savings"), ("Current", "Current")],
    )
    opening_balance = DecimalField(
        "Opening balance", validators=[DataRequired(), NumberRange(min=0, max=10000000)], places=2
    )
    submit = SubmitField("Link account")


class CreateUPIForm(FlaskForm):
    handle = StringField(
        "UPI handle",
        validators=[DataRequired(), Length(min=3, max=30), Regexp(r"^[a-zA-Z0-9._-]+$")],
    )
    provider = SelectField(
        "Provider",
        choices=[
            ("sbi", "@sbi"),
            ("hdfc", "@hdfc"),
            ("icici", "@icici"),
            ("axis", "@axis"),
            ("kotak", "@kotak"),
            ("payflow", "@payflow"),
            ("ybl", "@ybl"),
            ("okaxis", "@okaxis"),
        ],
    )
    account_id = SelectField("Link to bank account", coerce=int, validators=[DataRequired()])
    pin = PasswordField("6-digit UPI PIN", validators=[DataRequired(), Length(min=4, max=6)])
    is_primary = BooleanField("Set as primary")
    submit = SubmitField("Create UPI ID")
