from jinja2.exceptions import TemplateNotFound
import pyotp
import sass


from qually.helpers.route_imports import *

try:
    from flask_babel import _, format_datetime, force_locale
    import pypdf
    import reportlab
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except:
    pass

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
@cf_cache
def get_favicon_ico():
    return send_file('./assets/images/logo.png')

@app.get("/s3/organization/<oid>/<path:path>")
@logged_in
def get_s3_object_path(oid, path):

    if not g.user.organization_id==int(oid, 36):
        abort(404)

    file, mimetype = aws.download_file(f"organization/{oid}/{path}")
    
    return send_file(file, mimetype=mimetype)


@app.get("/s3/organization/<oid>/file/<fid>/<path:path>")
@logged_in
def get_s3_file_path(oid, path, fid=None):

    if not g.user.organization_id==int(oid, 36):
        abort(404)

    file_obj=g.user.organization.files.filter_by(id=int(fid, 36)).first()

    if not file_obj:
        abort(404)

    file, mimetype = aws.download_file(file_obj.s3_name)

    if mimetype!='application/pdf' or not isinstance(file_obj.owning_object, ItemRevision):
        return send_file(file, mimetype=mimetype)

    #if it's a PDF that's attached to an Item, stamp it

    #set the basic input and output
    reader=pypdf.PdfReader(file)
    writer=pypdf.PdfWriter()

    #Determine the stamp text
    with force_locale(g.user.organization.lang):
        if file_obj.owning_object.revision_number and file_obj.owning_object.status_utc:
            stamp_text = _("{name} Rev. {revision} | {status} {status_date} | Accessed {now}").format(
                name=file_obj.owning_object.item.name,
                revision=file_obj.owning_object.revision_number,
                status=file_obj.owning_object.status,
                status_date=format_datetime(datetime.datetime.fromtimestamp(file_obj.owning_object.status_utc), "dd MMMM yyyy"),
                changeorder=file_obj.owning_object.change.name,
                now=format_datetime(datetime.datetime.fromtimestamp(g.time), "dd MMMM yyyy")
                )

        elif file_obj.owning_object.revision_number:
            stamp_text = _("{name} Rev. {revision} | {status} | Accessed {now}").format(
                name=file_obj.owning_object.item.name,
                revision=file_obj.owning_object.revision_number,
                status=file_obj.owning_object.status,
                now=format_datetime(datetime.datetime.fromtimestamp(g.time), "dd MMMM yyyy")
                )

        elif file_obj.owning_object.change:
            stamp_text = _("{name} | Proposed revision | {changeorder}").format(
                name=file_obj.owning_object.item.name,
                changeorder=file_obj.owning_object.change.name,
                now=format_datetime(datetime.datetime.fromtimestamp(g.time), "dd MMMM yyyy")
                )

        else:
            stamp_text = _("{name} | Draft {t}").format(
                name=file_obj.owning_object.item.name,
                t=file_obj.owning_object.created_date
                )

    #create the stamp canvas
    packet=io.BytesIO()
    can=canvas.Canvas(packet, pagesize=letter)
    can.setFillColorRGB(1,0,0)
    can.setStrokeColorRGB(1,0,0)
    can.drawString(36,36, stamp_text)
    can.save()
    packet.seek(0)
    stamp_pdf=pypdf.PdfReader(packet)


    for index in list(range(0, len(reader.pages))):

        source_page=reader.pages[index]

        source_page.merge_page(stamp_pdf.pages[0])

        writer.add_page(source_page)

    buffer=io.BytesIO()
    writer.write_stream(buffer)
    buffer.seek(0)

    return send_file(buffer, mimetype=mimetype)

@app.get("/manifest.json")
@cf_cache
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

