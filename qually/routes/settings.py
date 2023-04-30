from qually.helpers.route_imports import *

@app.get("/settings/profile")
@logged_in
def get_settings_profile(page):
    return render_template("settings/profile.html")