"""
This daemon automatically removes photos that are too old.
"""

from caravel.storage import photos
from caravel import app


@app.route('/_internal/collect_garbage')
def collect_garbage():
    """Remove photos from GCS that are too old."""
    photos.collect_garbage()
    return "ok"
