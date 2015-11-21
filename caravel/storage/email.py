"""
Allows easy access to an SMTP server.
"""

import sendgrid

from caravel.storage import config

SENDER = "Marketplace Team <marketplace@lists.uchicago.edu>"

def send_mail(to, subject, html, text, reply_to=None, sender=SENDER):
    email = sendgrid.Mail()
    email.set_from(sender)
    email.add_to(to)
    if reply_to:
        email.set_replyto(reply_to)
    email.set_subject(subject)
    email.set_html(html)
    email.set_text(text)

    config.send_grid_client.send(email)