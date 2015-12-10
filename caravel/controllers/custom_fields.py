import wtforms
from markupsafe import Markup
from google.appengine.api import users
from flask import request

class PrincipalField(wtforms.StringField):
    """
    A PrincipalField is one that represents an email address.
    """

    def process_formdata(self, value):
        """
        Overrides the value sent in the form if asked.
        """

        user = users.get_current_user()
        if user:
            value = [user.email()]
        return super(PrincipalField, self).process_formdata(value)

    def __call__(self, **kwargs):
        """
        Renders a control with a Sign In button.
        """

        kwargs["class"] = kwargs.get("class", "") + " inline-user-control"
        kwargs["placeholder"] = "enter email..."

        if users.get_current_user():
            return Markup(
                "<p class='form-control-static'><strong>{}</strong> "
                "or <a href='{}' class='btn btn-success'>Sign out</a></p>"
            ).format(
                users.get_current_user().email(),
                users.create_logout_url(request.url),
            )

        else:
            return Markup(
                "<div><a href='{}' class='btn btn-success'>Sign in with "
                "CNetID</a>or {}</div>"
            ).format(
                users.create_login_url(request.url),
                super(PrincipalField, self).__call__(**kwargs),
            )
