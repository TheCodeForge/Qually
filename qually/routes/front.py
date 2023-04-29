from qually.helpers.route_imports import *

@app.get("/")
def get_home():
    return render_template("home.html")