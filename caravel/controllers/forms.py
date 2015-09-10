from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, DecimalField, FileField, FieldList, FormField
from wtforms.validators import Email


class BuyerForm(Form):
    email = StringField('Email (UChicago email preferred)', validators=[Email()])
    message = TextAreaField('Message')
    submit = SubmitField('Send')


class ImageEntry(Form):
    image = FileField('Image')


class SellerForm(Form):
    title = StringField('Listing Title')
    email = StringField('Email (UChicago email preferred)', validators=[Email()])
    price = DecimalField('Price', places=2)
    description = TextAreaField('Description')
    images = FieldList(FormField(ImageEntry), min_entries=5)
    submit = SubmitField('Post')