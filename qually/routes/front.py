from qually.helpers.route_imports import *

@app.get("/")
def get_home():
    return render_template("home.html")

@app.post("/settings/darkmode")
def post_settings_darkmode():

    session["dark_mode"] = not session.get("dark_mode", False)

    return "", 204