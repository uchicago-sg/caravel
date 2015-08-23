# Pull packages from vendor/ directory.
import sys; sys.path.insert(0, "vendor")

import state, live_migration
from flask import Flask, request, render_template, session

app = Flask(__name__)
app.secret_key = state.SECRET_KEY

@app.route("/")
def home_page():
    if not 'hits' in session:
        session['hits'] = 0
    session['hits'] += 1
    return render_template(
        "home_page.html",
        name="App Engine",
        hits=session['hits']
    )

@app.route("/_pull")
def pull_from_legacy_site():
    state.run_later(
        live_migration.pull_from_listing,
        permalink=request.args.get("permalink", "")
    )
    return "ok"

# TODO(fatlotus): add App-Engine-less version of the "state" module.
if __name__ == "__main__":
    app.run(debug=True)