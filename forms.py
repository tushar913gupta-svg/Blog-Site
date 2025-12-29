from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

class CreatePostForm(FlaskForm):
    title = StringField('Title', [DataRequired()])
    subtitle = StringField('Subtitle', [DataRequired()])
    img_url = StringField('Image URL', [URL()])
    body = CKEditorField('Body', [DataRequired()])
    submit = SubmitField('Submit')

class RegisterForm(FlaskForm):
    name = StringField("Name",[DataRequired()])
    email = StringField("Email",[DataRequired()])
    password = PasswordField("Password",[DataRequired()])
    submit = SubmitField("Sign Up")

class LoginForm(FlaskForm):
    email = StringField("Email", [DataRequired()])
    password = PasswordField("Password", [DataRequired()])
    submit = SubmitField("Login")

class AdminForm(FlaskForm):
    email = StringField("Email", [DataRequired()])
    submit = SubmitField("Make Admin")

class CommentForm(FlaskForm):
    comment = CKEditorField("Comment")
    submit = SubmitField("Submit")