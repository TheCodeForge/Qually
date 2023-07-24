from flask import g, session
import base64
import datetime
import io
import pyotp
import qrcode
import sass
from sqlalchemy import text

try:
    from flask_babel import gettext as _, format_datetime
except ModuleNotFoundError:
    pass

from qually.helpers.languages import LANGUAGES
from qually.helpers.timezones import TIMEZONES
from qually.helpers.security import generate_hash

from qually.classes import *

from qually.__main__ import app

@app.template_filter("app_config")
def app_config(x):
    return app.config.get(x)

@app.template_filter("csrf_token")
def logged_out_formkey(t):
    return generate_hash(f"{session['session_id']}")

@app.template_filter("full_link")
def full_link(url):

    return f"https://{app.config['SERVER_NAME']}{url}"

@app.template_filter('otp_qrcode')
def qrcode_filter(secret):
  
    mem=io.BytesIO()
    qr=qrcode.QRCode(qrcode.constants.ERROR_CORRECT_L)

    x=pyotp.TOTP(secret)

    qr.add_data(x.provisioning_uri(g.user.email, issuer_name=app.config["SITE_NAME"]))

    img=qr.make_image(
        fill_color=f"#{g.user.organization.color}",
        back_color="white",
    )

    img.save(
        mem, 
        format="PNG"
    )
    mem.seek(0)
    
    data=base64.b64encode(mem.read()).decode('ascii')
    return f"data:image/png;base64,{data}"


@app.template_filter('qrcode_img_data')
def qrcode_filter(x):
  
    mem=io.BytesIO()
    qr=qrcode.QRCode()
    qr.add_data(x)
    img=qr.make_image(
        fill_color=f"#{app.config['COLOR_PRIMARY']}",
        back_color="white",
    )
    img.save(
        mem, 
        format="PNG"
    )
    mem.seek(0)
    
    data=base64.b64encode(mem.read()).decode('ascii')
    return f"data:image/png;base64,{data}"

@app.template_filter('lang')
def languages(x):

    if x:
        return LANGUAGES[x]
    else:
        return LANGUAGES

@app.template_filter('tz')
def languages(x):

    return TIMEZONES

# @app.template_filter('css')
# def css(x):

#     name=f"{app.config['SYSPATH']}/assets/style/main.scss"
#     #print(name)
#     with open(name, "r") as file:
#         output = file.read()

#     # This doesn't use python's string formatting because
#     # of some odd behavior with css files

#     output = output.replace("{primary}", app.config['COLOR_PRIMARY'])
#     output = output.replace("{secondary}", app.config['COLOR_SECONDARY'])

#     #compile the regular css
#     output=sass.compile(string=output)

#     return output

@app.template_filter("debug")
def debug(x):

    print(x)
    return ""

@app.template_filter("sql_text")
def sql_text(x):

    return text(x)

@app.template_filter("roles")
def biz_roles(x):

    data={
        0: _("None"),
        1: _("Document Control"),
        2: _("Material Review Board"),
        3: _("Quality Management")
        }

    if x in data:
        return data[x]
    else:
        return data

@app.template_filter("date")
def jinja_date(x):
    return format_datetime(datetime.datetime.fromtimestamp(x), "dd MMMM yyyy")

@app.template_filter("datetime")
def jinja_date(x):
    return format_datetime(datetime.datetime.fromtimestamp(x), "dd MMMM yyyy HH:mm")

@app.template_filter("processes")
def jinja_processes(x):

    if x and x in ALL_PROCESSES:
        return ALL_PROCESSES[x]
    else:
        return ALL_PROCESSES


@app.template_filter("lambda")
def jinja_lambda(value, arg=False):

    if arg:
        return lambda x: value
    else:
        return lambda:value

@app.template_filter("list_comp")
def user_ids_filter(iterable, prop):

    return [getattr(x, prop) for x in iterable]