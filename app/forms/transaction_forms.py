from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class SendMoneyForm(FlaskForm):
    receiver_upi = StringField('Receiver UPI ID', validators=[DataRequired(), Length(max=100)])
    amount = DecimalField('Amount (₹)', validators=[DataRequired(), NumberRange(min=1, max=100000)], places=2)
    remarks = TextAreaField('Remarks (optional)', validators=[Length(max=255)])
    submit = SubmitField('Send Money')
