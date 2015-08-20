# Pull packages from vendor/ directory.
import sys; sys.path.insert(0, "vendor")

from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def home_page():
    return render_template("home_page.html", name="App Engine")

# Run a debug server if running locally.
if __name__ == "__main__":
    app.run(debug=True)