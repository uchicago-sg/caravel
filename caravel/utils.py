from caravel import app
from caravel.storage import entities
from flask import request

import math, time

@app.template_global()
def modify_search(add=[], remove=[]):
    """Adds and removes the given words from the query, returning the new ?q."""

    query = request.args.get('q', '').split()
    query = [x.strip() for x in query if x.strip()]

    for word in remove:
        if word in query:
            query.remove(word)

    for word in add:
        if word and word not in query:
            query.append(word)

    return " ".join(query)

@app.context_processor
def inject_categories():
    """Adds the categories into the view."""
    return {'categories': entities.Listing.CATEGORIES,
            'categories_dict': entities.Listing.CATEGORIES_DICT}

@app.template_filter("as_duration")
def as_duration(abs_time_in_seconds):
    """Returns a formatted string for this duration."""

    durations = (
        ('s', 1),
        ('m', 60),
        ('h', 60 * 60),
        ('d', 60 * 60 * 24),
        ('w', 60 * 60 * 24 * 7)
    )

    duration = time.time() - abs_time_in_seconds
    result = "now"

    for label, length in durations:
        if length > duration:
            break
        result = "{:.0f}{}".format(math.ceil(duration / length), label)

    return result
