from flask import g, session
import base64
import io
import pyotp
import qrcode
import sass

from qually.helpers.languages import LANGUAGES
from qually.helpers.timezones import TIMEZONES
from qually.helpers.security import generate_hash

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