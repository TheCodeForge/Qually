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

    if request.form.get("password") != request.form.get("confirm_password"):
        return toast_error("Passwords do not match.")
        
    if not request.form.get("name"):
        return toast_error("Your name is required")
        
    if not request.form.get("email"):
        return toast_error("Email address is required")

    if not request.form.get("org_name"):
        return toast_error("Organization name is required")

    existing=g.db.query(User).filter(User.email.ilike(request.form.get("email")))
    if existing:
        return toast_error("That email is already in use.")


    #Create new org with 30 day free trial
    new_org = Organization(
        name=request.form.get("org_name"),
        license_count=5,
        license_expire_utc = g.timestamp + 60*60*24*30
        )

    g.db.add(new_org)
    g.db.flush()

    new_user=User(
        name=request.form.get("name"),
        email=request.form.get("email"),
        passhash=generate_password_hash(request.form.get("password")),
        has_license=True,
        organization_id=new_org.id,
        is_org_admin=True
        )
    
    g.db.add(new_user)
    g.db.commit()

    return toast_redirect("/")

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