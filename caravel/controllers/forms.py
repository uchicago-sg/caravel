from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, DecimalField
from wtforms import FileField, FieldList, FormField, SelectMultipleField
from wtforms.validators import Email, DataRequired, ValidationError
from wtforms.widgets import ListWidget, CheckboxInput, HTMLString, html_params
from caravel import policy, app
from caravel.storage import photos
from flask_wtf.csrf import CsrfProtect

import logging

from caravel import policy, app
from caravel.storage import entities

class CheckboxSelectMultipleField(SelectMultipleField):
    option_widget = CheckboxInput()
    widget = ListWidget(prefix_label=False)

class StatefulFileField(StringField):
    FILLED_IN = '''<div class="thumbnail">
        <input {attributes}/><img src="{preview_url}"/>
        <div class="caption">
            <a class="btn btn-danger"
               onclick="removeThumbnail(this, {id!r})">Remove</a>
        </div>
    </div>'''
    UNFILLED = '<input {attributes}/>'

    def widget(self, field, **kwargs):
        try:
            kwargs.update(id=field.name, name=field.name)

            if field.data:
                # Display a preview of what's already present, plus a link to
                # reset the input type with JavaScript.
                kwargs.update(type='hidden', value=field.data)
                return HTMLString(self.FILLED_IN.format(
                    attributes=html_params(**kwargs),
                    preview_url=photos.public_url(field.data),
                    id=str(kwargs['id'])
                ))

            else:
                # Display just a file input.
                kwargs.update(type='file')
                return HTMLString(self.UNFILLED.format(
                    attributes=html_params(**kwargs)))
        
        except Exception, e:
            logging.exception(e)

class BuyerForm(Form):
    buyer = StringField("Email", description="UChicago Email Preferred",
                validators=[Email()])
    message = TextAreaField("Message")
    submit = SubmitField("Send")

    def validate_buyer(self, field):
        if not policy.is_authorized_buyer(field.data or ""):
            raise ValidationError("Only @uchicago.edu addresses are allowed.")

class ImageEntry(Form):
    image = StatefulFileField("Image")

class EditListingForm(Form):
    title = StringField("Listing Title",
                validators=[DataRequired()])
    price = DecimalField("Price", places=2, default=0)
    description = TextAreaField("Description", validators=[DataRequired()])
    categories = CheckboxSelectMultipleField("Categories",
                    choices=[(x, y)
                        for x, y in entities.Listing.CATEGORIES if x != "free"],
                    validators=[DataRequired()])
    photos = FieldList(FormField(ImageEntry), min_entries=5)
    submit = SubmitField("Post")

class NewListingForm(EditListingForm):
    seller = StringField("Email", description="UChicago Email Required",
                validators=[Email()])

    def validate_seller(self, field):
        if not policy.is_authorized_seller(field.data or ""):
            raise ValidationError("Only @uchicago.edu addresses are allowed.")

CsrfProtect(app)
