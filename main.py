# Pull packages from vendor/ directory.
import sys; sys.path.insert(0, "vendor")

import state, live_migration

from flask import Flask, request, render_template, session, jsonify
app = Flask(__name__)
app.secret_key = state.SECRET_KEY

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/_pull")
def pull_from_legacy_site():
    state.run_later(
        live_migration.pull_from_listing,
        permalink=request.args.get("permalink", "")
    )
    return "ok"

@app.route("/<permalink>")
def show(permalink):
    listing = state.Listing.get_by_id(permalink)
    return render_template("listing_show.html")

# Run a debug server if running locally.
if __name__ == "__main__":
    app.run(debug=True)
