from caravel.storage import config

import json
import urllib
from flask import request

def send_chat(text, username=None, icon_url=None):
    """
    Sends the given message to the general Slack channel. URLs can be specified
    in the message by encoding them in brackets, i.e. so that

      click <http://target|here> for listings  
         ->
      click <a href="http://target">here</a> for listings

    """

    url = config.slack_url
    if not url:
        return

    payload = {"text": text}

    if username:
        payload["username"] = username

    if icon_url:
        payload["icon_url"] = icon_url

    urllib.urlopen(url, json.dumps(payload))
