from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
from app.models.user import User


class RegisterForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=50)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=50)])
    phone = StringField(
        "Phone",
        validators=[DataRequired(), Length(min=10, max=15), Regexp(r"^[0-9+\- ]+$")],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=4, max=64)])
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Create account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("Email already registered.")

    def validate_phone(self, field):
        phone = field.data.strip()
        if User.query.filter_by(phone=phone).first():
            raise ValidationError("Phone already registered.")


class LoginForm(FlaskForm):
    login = StringField("Email or phone", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Sign in")
