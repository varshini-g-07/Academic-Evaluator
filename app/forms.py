from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, FloatField, FieldList, FormField, PasswordField, EmailField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Length, EqualTo

class TeacherRegForm(FlaskForm):
    teacherName = StringField("Enter Name: ", validators=[DataRequired(), Length(3, 25)])
    email = EmailField("Email ID: ", validators=[DataRequired()])
    password = PasswordField("Password: ", validators=[DataRequired(), Length(8, 30)])
    submit = SubmitField("Register")

class TeacherLoginForm(FlaskForm):
    email = EmailField("Email ID: ", validators=[DataRequired()])
    password = PasswordField("Password: ", validators=[DataRequired(), Length(8, 30)])
    submit = SubmitField("Login")

class AddStudent(FlaskForm):
    studentName = StringField("Enter Name: ", validators=[DataRequired(), Length(3, 25)])
    rollno = IntegerField("Roll Number: ", validators=[DataRequired(), NumberRange(100000000, 999999999)])
    submit = SubmitField("Submit Details")

class StudentLoginForm(FlaskForm):
    rollno = IntegerField("Roll Number: ", validators=[DataRequired(), NumberRange(100000000, 999999999)])
    password = PasswordField("Password: ", validators=[DataRequired(), Length(8, 30)])
    submit = SubmitField("Login")

class PasswordChange(FlaskForm):
    current_pass = PasswordField("Enter current password: ", validators=[DataRequired()])
    new_pass = PasswordField("Enter new password: ", validators=[DataRequired()])
    confirm_pass = PasswordField("Confirm new password: ", validators=[DataRequired(), EqualTo('new_pass')])
    submit = SubmitField('Submit')

class ItemForm(FlaskForm):
    sub = StringField("Enter subject name: ", validators=[DataRequired()])
    credits = FloatField("Enter credits for subject: ", validators=[DataRequired(), NumberRange(0, 5)])
    marks = FloatField("Enter end-semester marks (out of 100): ", validators=[DataRequired(), NumberRange(0, 100)])
    internal_marks = FloatField("Enter internal marks (out of 40): ", validators=[DataRequired(), NumberRange(0, 40)])

class CgpaForm(FlaskForm):
    items = FieldList(FormField(ItemForm), min_entries=1)
    add_subject = SubmitField("Add Subject")
    submit = SubmitField("Submit")
    reset = SubmitField('Reset')