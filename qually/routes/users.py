from qually.helpers.route_imports import *

@app.get("/user/<uid>")
@logged_in
def get_user_uid(uid):

    user=get_account(uid)

    return render_template(
        "/userpage.html",
        user=user,
        ROLES=ROLES
        )