from jinja2.exceptions import TemplateNotFound
import pyotp
import sass

from qually.helpers.route_imports import *

# take care of misc pages that never really change (much)

@app.get("/assets/style/<color1>/<color2>.css")
@cf_cache
@cache.memoize()
def main_css(color1, color2, n=None):

    name=f"{app.config['SYSPATH']}/assets/style/main.scss"
    #print(name)
    with open(name, "r") as file:
        output = file.read()

    # This doesn't use python's string formatting because
    # of some odd behavior with css files
    try:
        i=int(color1, 16)
        i=int(color2, 16)
    except:
        color1=app.config['COLOR_PRIMARY']
        color2=app.config['COLOR_SECONDARY']

    output = output.replace("{primary}", color1)
    output = output.replace("{secondary}", color2)

    #compile the regular css
    output=sass.compile(string=output)

    resp = Response(output, mimetype='text/css')

    del output
    return resp

@app.get('/assets/<path:path>')
@limiter.exempt
@cf_cache
def static_service(path):

    try:
        resp = make_response(send_file(safe_join('./assets', path)))
    except FileNotFoundError:
        abort(404)
    except IsADirectoryError:
        abort(404)

    if request.path.endswith('.css'):
        resp.headers.add("Content-Type", "text/css")
    elif request.path.endswith(".js"):
        resp.headers.add("Content-Type", "text/javascript")
    return resp


@app.get("/robots.txt")
def robots_txt():

    # banned_robot_uas = ["Mozilla", "Chrome", "Safari"]

    # if request.headers.get("User-Agent") and not any([x in request.headers["User-Agent"] for x in banned_robot_uas]):
    #     return make_response("User-Agent: *\nDisallow: /", mimetype="text/plain")

    return send_file("./assets/robots.txt")

@app.get("/help/<path:path>")
def help_path(path):
    try:
        to_render=safe_join("help/", f"{path}.html")
        #debug(to_render)
        return render_template(to_render)
    except TemplateNotFound:
       abort(404)


@app.get("/help")
def help_home():
    return render_template("help.html")

@app.get("/favicon.ico")
def get_favicon_ico():
    return send_file('./assets/images/logo.png')

@app.get("/s3/organization/<oid>/<path:path>")
@logged_in
def get_s3_object_path(oid, path):


    if not g.user.organization_id==int(oid, 36):
        abort(404)

    file, mimetype = aws.download_file(f"organization/{oid}/{path}")

    return send_file(file, mimetype=mimetype)

@app.get("/manifest.json")
def get_manifest_json():
    data={
      "name": app.config["SITE_NAME"],
      "short_name": app.config["SITE_NAME"],
      "start_url": f"https://{app.config['SERVER_NAME']}",
      "scope": "/",
      "display": "fullscreen",
      "background_color": f"#{app.config['COLOR_PRIMARY']}",
      "description": "Your data, our processes, total quality"
    }
    return jsonify(data)

# @app.route("/help/docs")
# @cache.memoize(10)
# def docs():

#     class Doc():

#         def __init__(self, **kwargs):
#             for entry in kwargs:
#                 self.__dict__[entry]=kwargs[entry]

#         def __str__(self):

#             return f"{self.method.upper()} {self.endpoint}\n\n{self.docstring}"

#         @property
#         def docstring(self):
#             return self.target_function.__doc__ if self.target_function.__doc__ else "[doc pending]"

#         @property
#         def docstring_html(self):
#             return mistletoe_markdown(self.docstring)

#         @property
#         def resource(self):
#             return self.endpoint.split('/')[1]

#         @property
#         def frag(self):
#             tail=self.endpoint.replace('/','_')
#             tail=tail.replace("<","")
#             tail=tail.replace(">","")
#             return f"{self.method.lower()}{tail}"
        
        

#     docs=[]

#     for rule in app.url_map.iter_rules():

#         if not rule.rule.startswith("/api/v2/"):
#             continue

#         endpoint=rule.rule.split("/api/v2")[1]

#         for method in rule.methods:
#             if method not in ["OPTIONS","HEAD"]:
#                 break

#         new_doc=Doc(
#             method=method,
#             endpoint=endpoint,
#             target_function=app.view_functions[rule.endpoint]
#             )

#         docs.append(new_doc)

#     method_order=["POST", "GET", "PATCH", "PUT", "DELETE"]

#     docs.sort(key=lambda x: (x.endpoint, method_order.index(x.method)))

#     fulldocs={}

#     for doc in docs:
#         if doc.resource not in fulldocs:
#             fulldocs[doc.resource]=[doc]
#         else:
#             fulldocs[doc.resource].append(doc)

#     return render_template("docs.html", docs=fulldocs, v=None)

