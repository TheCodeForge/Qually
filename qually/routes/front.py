from qually.helpers.languages import LANGUAGES
from qually.helpers.route_imports import *

@app.get("/")
def get_home():

    if g.user:
        return render_template("dashboard.html")
    else:
        return render_template("home.html")

@app.post("/prefs/dark_mode")
def post_settings_dark_mode():

    session["dark_mode"] = not session.get("dark_mode", False)

    return "", 204

@app.post("/prefs/lang/<lang>")
def post_prefs_lang_lang(lang):

    if lang not in LANGUAGES.values():
        return toast_error(_("That language is not currently supported."))

    session["lang"] = lang
    return "", 204