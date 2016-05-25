import flask_wtf
import wtforms
from wtforms.fields import (StringField, SubmitField, SelectMultipleField,
                            DecimalField, FieldList, FormField, TextAreaField)
from wtforms.widgets import CheckboxInput, ListWidget
from wtforms.validators import DataRequired, Email
from caravel.controllers.custom_fields import (PrincipalField, PhotoField,
                                               OnlyValid, MatchesPrincipal,
                                               AffiliationField)
from caravel import model


class CheckboxesField(SelectMultipleField):
    option_widget = CheckboxInput()
    widget = ListWidget(prefix_label=False)


class PhotoEntry(wtforms.Form):
    image = PhotoField("Image")


class ListingForm(flask_wtf.Form):
    title = StringField("Title", validators=[DataRequired()])
    body = TextAreaField("Body", validators=[DataRequired()])
    price = DecimalField("Price", places=2, default=0)
    recaptcha = flask_wtf.RecaptchaField()

    categories = CheckboxesField(
        "Categories",
        choices=model.Listing.CATEGORIES_LIST,
        validators=[DataRequired()]
    )

    uploaded_photos = FieldList(
        FormField(PhotoEntry),
        min_entries=5
    )


class NewListingForm(ListingForm):
    affiliation = AffiliationField("Affiliation", validators=[DataRequired()])
    principal = PrincipalField("Email", validators=[DataRequired()])
    submit = SubmitField("Create")


class EditListingForm(ListingForm):
    principal = PrincipalField("Seller", validators=[MatchesPrincipal()])
    submit = SubmitField("Update")


class InquiryForm(flask_wtf.Form):
    affiliation = AffiliationField("Affiliation", validators=[DataRequired()])
    principal = PrincipalField("Email", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    recaptcha = flask_wtf.RecaptchaField()
    submit = SubmitField("Send Inquiry")
