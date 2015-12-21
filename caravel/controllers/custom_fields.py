from google.appengine.api import users

import re
import wtforms
from wtforms import widgets, ValidationError

from markupsafe import Markup
from flask import request
from werkzeug import FileStorage

from caravel import model, utils

class OnlyValid(object):
    """Validates that the credential is correct."""

    def __call__(self, form, field):
        """Ensure that the Principal passed in is valid."""

        if not field.data or not field.data.valid:
            raise ValidationError("Invalid credential.")

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

        device = utils.Device.from_request(request)
        user = users.get_current_user()
        if user:
            self.data = utils.Principal(user.email(), device, "GOOGLE_APPS")
        elif ((not self.requires_validation) and values and
              re.match(r'^[^@]+@[^@]+$', values[0])):
            self.data = utils.Principal(values[0], device, "EMAIL")
        else:
            self.data = None

    def _value(self):
        """Returns the user for this user."""
        return self.data.email if self.data else ""

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
                users.create_logout_url(request.url),
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
                alternative = Markup(" or {}").format(
                    super(PrincipalField, self).__call__(**kwargs),
                )

            return Markup(
                "<div><a href='{}' class='btn btn-success'>Sign in with "
                "CNetID</a>{}</div>"
            ).format(users.create_login_url(request.url), alternative)

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