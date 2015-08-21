# Pull packages from vendor/ directory.
import sys; sys.path.insert(0, "vendor")

from state import SECRET_KEY

from flask import Flask, render_template, session

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.route("/")
def home_page():
    if not 'hits' in session:
        session['hits'] = 0
    session['hits'] += 1
    return render_template("home_page.html", name="App Engine", hits=session['hits'])

# Run a debug server if running locally.
if __name__ == "__main__":
    app.run(debug=True)