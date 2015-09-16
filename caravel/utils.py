from caravel import app

import math, time

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