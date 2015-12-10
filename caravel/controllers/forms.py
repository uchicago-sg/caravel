from flask.ext.wtf import Form, RecaptchaField
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
from caravel.controllers import custom_fields

class CheckboxesField(SelectMultipleField):
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

class ValidatedForm(Form):
    """
    A ValidatedForm is one that has validation separate from its fields.

    Validation is performed in the post_validate() function right before the 
    form is about to be saved.
    """

    def validate(self):
        """Override the default validation hook."""

        result = super(ValidatedForm, self).validate()
        if result and hasattr(self, "post_validate"):
            try:
                self.post_validate()
            except ValidationError, e:
                
                # Add the error to the first visible form entry.
                for field in self._fields.values():
                    if field.widget.input_type != "hidden":
                        field.errors.append(str(e))
                        break
                else:
                    raise e

                # Recompute self.errors, in case it isn't showing up.
                self._errors = None
                return False
        return result

class BuyerForm(ValidatedForm):
    buyer = custom_fields.PrincipalField("Email",
                validators=[DataRequired(), Email()])
    message = TextAreaField("Message")
    captcha = RecaptchaField()
    submit = SubmitField("Send")

class ImageEntry(Form):
    image = StatefulFileField("Image")

class EditListingForm(ValidatedForm):
    CHOICES = entities.Listing.CATEGORIES[:]
    CHOICES.remove(("price:free", "Free"))
    
    title = StringField("Listing Title", validators=[DataRequired()])
    price = DecimalField("Price", places=2, default=0)
    description = TextAreaField("Description", validators=[DataRequired()])
    categories = CheckboxesField("Categories", choices=CHOICES,
                                               validators=[DataRequired()])
    photos = FieldList(FormField(ImageEntry), min_entries=5)
    submit = SubmitField("Post")

class NewListingForm(EditListingForm):
    seller = custom_fields.PrincipalField("Email",
                                  validators=[DataRequired(), Email()])

CsrfProtect(app)
