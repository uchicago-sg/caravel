from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, DecimalField, FileField, FieldList
from wtforms.validators import Email

class BuyerForm(Form):
    email = StringField('Email (UChicago email preferred)', validators=[Email()])
    message = TextAreaField('Message')
    submit = SubmitField('Send')
