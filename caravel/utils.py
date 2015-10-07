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

@app.template_filter("category_colors")
def category_colors(category):
    category_colors = {
                       "apartments":"#a52a2a",
                       "subleases": "#ff1493",
                       "appliances": "#ff8c00",
                       "bikes": "#6495ed",
                       "cars": "#ff0000",
                       "electronics": "#9370db",
                       "employment": "#008000",
                       "furniture": "#ff7f50",
                       "miscelleneous": "#808080",
                       "services": "#202baa",
                       "wanted": "#40e0d0"
                    }
    return category_colors[category]

