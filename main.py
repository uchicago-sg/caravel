# Pull packages from vendor/ directory.
import sys; sys.path.insert(0, "vendor")

import models
import search
import live_migration

from flask import Flask, request, render_template, session, jsonify
app = Flask(__name__)
app.secret_key = models.SECRET_KEY

@app.route("/")
def index():
    listings = search.run_query(request.args.get("q"))
    return render_template("index.html", listings=listings)

@app.route("/<permalink>")
def show(permalink):
    listing = models.Listing.get_by_id(permalink)
    return render_template("listing_show.html", listing=listing)

@app.route("/<permalink>/edit")
def form(permalink):
    listing = models.Listing.get_by_id(permalink)
    return render_template("listing_form.html", listing=listing)

@app.route("/_pull")
def pull_from_legacy_site():
    models.run_later(
        live_migration.pull_from_listing,
        permalink=request.args.get("permalink", "")
    )
    return "ok"

# Run a debug server if running locally.
if __name__ == "__main__":
    app.run(debug=True)
