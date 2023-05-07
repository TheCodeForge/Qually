from qually.helpers.route_imports import *
from flask_babel import gettext as _, ngettext as N_

@app.get("/")
def get_home():
    return render_template("home.html")

@app.post("/settings/dark_mode")
def post_settings_dark_mode():

    session["dark_mode"] = not session.get("dark_mode", False)

    return "", 204