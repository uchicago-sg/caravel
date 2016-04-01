"""
This daemon automatically removes photos that are too old.
"""

from caravel import app, model
from google.appengine.api import users


@app.route('/_internal/collect_garbage')
def collect_garbage():
    if not users.is_current_user_admin():
        return "???"

    model.Photo.remove_old_photos()

    return "ok"
