# Pull packages from vendor/ directory.
import sys; sys.path.insert(0, "vendor")

import models
import search
import live_migration
import itertools

from flask import Flask, request, render_template, session, jsonify
app = Flask(__name__)
app.secret_key = models.SECRET_KEY

@app.route("/")
def index():
    listings = itertools.islice(search.run_query(request.args.get("q")), 0, 40)
    return render_template("index.html", listings=listings)

@app.route("/<permalink>")
def show(permalink):
    listing = search.lookup_listing(permalink)
    if listing:
        return render_template("listing_show.html", listing=listing)
    else:
        return "404"

@app.route("/<permalink>/edit")
def form(permalink):
    listing = search.lookup_listing(permalink)
    if listing:
        return render_template("listing_form.html", listing=listing)
    else:
        return "404"

@app.route("/_pull")
def pull_from_legacy_site():
    models.run_later(
        live_migration.pull_from_listing,
        permalink=request.args.get("permalink", "")
    )
    return "ok"

@app.route("/favicon.ico")
def block_favicons():
    return "go away"

# Run a debug server if running locally.
if __name__ == "__main__":
    app.run(debug=True)
