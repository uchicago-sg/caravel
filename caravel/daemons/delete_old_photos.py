"""
This daemon automatically removes photos that are too old.
"""

from caravel import app, model
from google.appengine.api import users


@app.route('/_internal/collect_garbage')
def collect_garbage():
    model.Photo.remove_old_photos()

    return "ok"
