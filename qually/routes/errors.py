from qually.helpers.route_imports import *

# Errors


@app.errorhandler(401)
def error_401(e):
    return render_template('errors/401.html'), 401

@app.errorhandler(PaymentRequired)
def error_402(e):
    return render_template('errors/402.html'), 402

@app.errorhandler(403)
def error_403(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def error_404(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(405)
def error_405(e):
    return render_template('errors/405.html'), 405


@app.errorhandler(409)
def error_409(e):
    return render_template('errors/409.html'), 409


@app.errorhandler(410)
def error_410(e):
    return render_template('errors/410.html'), 410


@app.errorhandler(413)
def error_413(e):
    return render_template('errors/413.html'), 413

@app.errorhandler(418)
def error_418(e):
    return render_template('errors/418.html'), 418

@app.errorhandler(422)
def error_422(e):
    return render_template('errors/422.html'), 422

@app.errorhandler(429)
def error_429(e):
    return render_template('errors/429.html'), 429


@app.errorhandler(451)
@api()
def error_451(e):
    return render_template('errors/451.html'), 451

@app.errorhandler(500)
@api()
def error_500(e):
    try:
        g.db.rollback()
    except AttributeError:
        pass

    return render_template('errors/500.html'), 500

@app.errorhandler(503)
def error_503(e):
    try:
        g.db.rollback()
    except AttributeError:
        pass

    return render_template('errors/503.html'), 503

@app.route("/error/<eid>", methods=["GET"])
@auth_desired
def error_all_preview(eid):
     return render_template(safe_join('errors', f"{eid}.html"))