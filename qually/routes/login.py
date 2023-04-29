from werkzeug.security import generate_password_hash, check_password_hash
import re
from qually.helpers.route_imports import *

valid_password_regex = re.compile("^.{8,100}+$")
valid_email_regex    = re.compile("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

@app.get("/register")
@not_logged_in
def get_register():
    return render_template("/register.html")

@app.post("/register")
@not_logged_in
def post_register():



@app.get("/sign_in")
@not_logged_in
def get_login():
    return render_template("/sign_in.html")

@app.post("/logout")
@logged_in
def post_logout():
    session.pop("user_id")
    return redirect("/")

@app.get("/set_otp")
@logged_in
def get_set_otp():

    if g.user.otp_secret:
        return redirect("/")

    otp_secret=pyotp.random_base32()
    recovery = compute_otp_recovery_code(g.user, otp_secret)
    recovery=" ".join([recovery[i:i+5] for i in range(0,len(recovery),5)])

    return render_template(
        "set_otp.html",
        otp_secret = otp_secret,
        recovery = recovery,
        )

@app.post("/set_otp")
@logged_in
def post_set_otp():
    otp_secret = request.form.get("otp_secret")
    code = request.form.get("otp_code")

    totp = pyotp.TOTP(otp_secret)

    if not werkzeug.security.check_password_hash(g.user.pw_hash, request.form.get("password")):
        return toast_error("Incorrect password", 401)

    if not totp.verify(code):
        return toast_error("Incorrect code", 401)

    g.user.otp_secret=otp_secret
    g.db.add(g.user)
    g.db.commit()

    return toast_redirect("/")