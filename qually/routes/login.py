from flask import redirect, render_template

from qually.__main__ import app

@app.get("/login")
def get_login():

    if g.user:
        return redirect("/")

    return render_template("/login.html")

@app.post("/logout")
def post_logout():
    session.pop("user_id")
    return redirect("/")