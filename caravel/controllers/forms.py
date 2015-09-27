from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, DecimalField
from wtforms import FileField, FieldList, FormField
from wtforms.validators import Email, DataRequired, ValidationError
from caravel import policy, app
from flask_wtf.csrf import CsrfProtect

class BuyerForm(Form):
    buyer = StringField("Email", description="UChicago Email Preferred",
                validators=[Email()])
    message = TextAreaField("Message")
    submit = SubmitField("Send")

    def validate_buyer(self, field):
        if not policy.is_authorized_buyer(field.data or ""):
            raise ValidationError("Only @uchicago.edu addresses are allowed.")

class ImageEntry(Form):
    image = FileField("Image")

class EditListingForm(Form):
    title = StringField("Listing Title",
                validators=[DataRequired()])
    price = DecimalField("Price", places=2,
                validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    photos = FieldList(FormField(ImageEntry), min_entries=5)
    submit = SubmitField("Post")

class NewListingForm(EditListingForm):
    seller = StringField("Email", description="UChicago Email Required",
                validators=[Email()])

    def validate_seller(self, field):
        if not policy.is_authorized_seller(field.data or ""):
            raise ValidationError("Only @uchicago.edu addresses are allowed.")

CsrfProtect(app)
