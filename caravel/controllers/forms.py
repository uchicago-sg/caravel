from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, DecimalField
from wtforms import FileField, FieldList, FormField, SelectMultipleField
from wtforms.validators import Email, DataRequired, ValidationError
from wtforms.widgets import ListWidget, CheckboxInput
from caravel import policy, app
from flask_wtf.csrf import CsrfProtect

CATEGORIES = [
    ("apartments", "Apartments"),
    ("subleases", "Subleases"),
    ("appliances", "Appliances"),
    ("bikes", "Bikes"),
    ("books", "Books"),
    ("cars", "Cars"),
    ("electronics", "Electronics"),
    ("employment", "Employment"),
    ("furniture", "Furniture"),
    ("miscellaneous", "Miscellaneous"),
    ("services", "Services"),
    ("wanted", "Wanted"),
]

class CheckboxSelectMultipleField(SelectMultipleField):
    option_widget = CheckboxInput()
    widget = ListWidget(prefix_label=False)

class BuyerForm(Form):
    email = StringField("Email", description="UChicago email preferred",
                validators=[Email()])
    message = TextAreaField("Message")
    submit = SubmitField("Send")

class ImageEntry(Form):
    image = FileField("Image")

class EditListingForm(Form):
    title = StringField("Listing Title",
                validators=[DataRequired()])
    price = DecimalField("Price", places=2,
                validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    categories = CheckboxSelectMultipleField("Categories", choices=CATEGORIES,
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
