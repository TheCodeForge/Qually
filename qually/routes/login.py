from qually.__main__ import app

@app.post("/logout")
def post_logout():
    session.pop("user_id")
    return redirect("/")