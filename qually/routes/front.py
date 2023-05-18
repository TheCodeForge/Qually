from qually.helpers.languages import LANGUAGES
from qually.helpers.route_imports import *
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    pass

@app.get("/")
def get_home():

    if not g.user:
        return render_template("home.html")

    ncmr_conditions=[NCMR.assignee_id==g.user.id]
    if g.user.is_doc_control:
        ncmr_conditions.append(NCMR._status.in_([1,4]))
    if g.user.is_mrb:
        ncmr_conditions.append(NCMR._status==2)

    data={
            "ncmr": {
            "name":_("Non-Conforming Material Reports"),
            "owned":g.user.organization.ncmrs.filter(NCMR.owner_id==g.user.id, NCMR._status<100).all(),
            "assigned":g.user.organization.ncmrs.filter(or_(NCMR._assignment_query_args(), NCMR._status<100)).all()
        # },
        #     "capa": {
        #     "name":_("Corrective and Preventive Actions"),
        #     "owned":[],
        #     "assigned":[]
        }
    }
    return render_template("dashboard.html", data=data)

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