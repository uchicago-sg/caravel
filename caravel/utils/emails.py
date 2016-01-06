"""
Allows easy access to an SMTP server.
"""

import sendgrid
import logging

SENDER = "Marketplace Team <marketplace@lists.uchicago.edu>"


def send_mail(to, subject, html, text, reply_to=None, sender=SENDER):
    """
    Sends an email to the given principals.
    """

    from caravel.utils import principals

    # Verify that we are not sending spam to people.
    if not (isinstance(to, principals.Principal) and to.valid):
        raise ValueError("{!r} does not consented to email.".format(to))

    # Verify that we are not sending spam from people.
    if reply_to:
        if not (isinstance(reply_to, principals.Principal) and reply_to.valid):
            raise ValueError("{!r} has not consented to send email."
                             .format(reply_to))

    # Actually send the message to the user.
    _send_raw_mail(
        to=to.email,
        subject=subject,
        html=html,
        text=text,
        reply_to=reply_to.email if reply_to else None,
        sender=sender
    )


def _send_raw_mail(to, subject, html, text, reply_to=None, sender=SENDER):
    logging.debug("SendMail(to={!r}, subject={!r})".format(to, subject))

    from caravel.storage import config

    email = sendgrid.Mail()
    email.set_from(sender)
    email.add_to(to)
    if reply_to:
        email.set_replyto(reply_to)
    email.set_subject(subject)
    email.set_html(html)
    email.set_text(text)

    config.send_grid_client.send(email)
