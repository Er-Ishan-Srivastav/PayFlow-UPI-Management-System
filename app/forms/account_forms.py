from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

class LinkBankForm(FlaskForm):
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(max=100)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=8, max=20)])
    ifsc_code = StringField('IFSC Code', validators=[DataRequired(), Length(min=11, max=11), Regexp(r'^[A-Z]{4}0[A-Z0-9]{6}$')])
    account_type = SelectField('Account Type', choices=[('Savings', 'Savings'), ('Current', 'Current')])
    is_primary = BooleanField('Set as Primary Account')
    submit = SubmitField('Link Bank Account')

class CreateUPIForm(FlaskForm):
    upi_handle = StringField('UPI Handle (without @payflow)', validators=[DataRequired(), Length(min=3, max=50)])
    bank_account_id = SelectField('Link to Bank Account', coerce=int, validators=[DataRequired()])
    is_primary = BooleanField('Set as Primary UPI')
    submit = SubmitField('Create UPI ID')
