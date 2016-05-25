from google.appengine.api import users

import re
import threading

import wtforms
from wtforms import widgets, ValidationError

from markupsafe import Markup
from flask import request, session
from werkzeug import FileStorage

from caravel import model, utils


class OnlyValid(object):

    """Validates that the credential is correct."""

    def __call__(self, form, field):
        """Ensure that the Principal passed in is valid."""

        if not field.data or not field.data.valid:
            raise ValidationError("Invalid credential.")


class MatchesPrincipal(threading.local):

    """Ensures that only the existing Principal is used."""

    def __init__(self):
        self.principal = None

    def __call__(self, form, field):
        """Ensure that only the given user is used for authentication."""

        if not self.principal:
            raise Exception("No principal specified.")

        if not field.data or not field.data.can_act_as(self.principal):
            if not field.data:
                raise ValidationError("Please enter an email.")
            elif field.data.email == self.principal.email:
                raise ValidationError("Please sign in with your CNetID.")
            else:
                raise ValidationError("Please use the same account for edits.")


class AffiliationField(wtforms.SelectField):
    """
    An AffiliationField is one that represents an individual's
    affiliation.
    """

    def __init__(self, label, **kwargs):
        kwargs["choices"] = ([("", "(Select Affiliation...)")] +
                             model.Listing.AFFILIATIONS)
        kwargs["default"] = lambda: session.get("affiliation")

        super(AffiliationField, self).__init__(label, **kwargs)

    def __call__(self, **kwargs):
        kwargs["data-affiliation"] = "value"
        return super(AffiliationField, self).__call__(**kwargs)

    def process_formdata(self, values):
        """Overrides the value sent in the form if asked."""

        super(AffiliationField, self).process_formdata(values)

        if self.data:
            session["affiliation"] = self.data


class PrincipalField(wtforms.StringField):
    """A PrincipalField is one that represents an email address."""

    def __init__(self, label, **kwargs):
        """Initialize this field, adding the requires_validation field."""

        if "validated" in kwargs:
            self.requires_validation = kwargs["requires_validation"]
            del kwargs["requires_validation"]
        else:
            self.requires_validation = False

        return super(PrincipalField, self).__init__(label, **kwargs)

    def process_formdata(self, values):
        """Overrides the value sent in the form if asked."""

        # Extract data into a principal
        email = None
        if not self.requires_validation and values:
            email = values[0]
        self.data = utils.Principal.from_request(request, email)

        # Persist email in a session variable
        if self.data:
            session["email"] = self.data.email

    def _value(self):
        """Returns the user for this user."""
        return self.data.email if self.data else session.get("email", "")

    def __call__(self, **kwargs):
        """Renders a control with a Sign In button."""

        if users.get_current_user():
            kwargs["type"] = "hidden"

            return Markup(
                "<p class='form-control-static'><strong>{}</strong> "
                "(<a href='{}'>Logout</a>)</p>"
                "{}"
            ).format(
                users.get_current_user().email(),
                users.create_logout_url(request.url.encode("utf-8")),
                super(PrincipalField, self).__call__(**kwargs)
            )

        else:
            kwargs["class"] = kwargs.get("class", "") + " inline-user-control"
            kwargs["placeholder"] = "enter email..."

            # Only add -or [ enter email ] if we can.
            alternative = ""
            for validator in self.validators:
                if isinstance(validator, OnlyValid):
                    break
            else:
                alternative = Markup(
                    "<span class='accessibility'> or </span>{}").format(
                    super(PrincipalField, self).__call__(**kwargs), )

            return Markup(
                "<div><a href='{}' class='signin btn btn-success'>Sign in with "
                "CNetID</a>{}</div>"
            ).format("/oshalogin", alternative)
            # users.create_login_url(request.url)


class PhotoField(wtforms.StringField):

    """A PhotoField represents a photo object stored in Cloud Storage."""

    def process_formdata(self, values):
        """Process an external photo value."""

        for value in values:
            if not value:
                continue

            if not isinstance(value, FileStorage):
                self.data = model.Photo(value)
                break
            elif value.filename:
                self.data = model.Photo.from_image_data(value.read())
                break
        else:
            self.data = None

    def _value(self):
        """Return the photo as a serializable value"""
        return self.data.path if self.data else ""

    def widget(self, field, **kwargs):
        """Render this file input as a removable file upload control."""

        if self.data:
            kwargs["type"] = "hidden"

            return Markup("""
                <div class="thumbnail">
                  {} <img src="{}"/>
                  <div class="caption">
                    <a class="btn btn-danger"
                       onclick="removeThumbnail(this, {!r})">Remove</a>
                  </div>
                </div>
            """).format(
                super(PhotoField, self).widget(field, **kwargs),
                self.data.public_url("large"), str(field.name)
            )
        else:
            kwargs["type"] = "file"
            return super(PhotoField, self).widget(field, **kwargs)
