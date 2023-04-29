import base64
import io
import qrcode

from qually.helpers.security import generate_hash

from qually.__main__ import app

@app.template_filter("app_config")
def app_config(x):
    return app.config.get(x)

@app.template_filter("csrf_token")
def logged_out_formkey(t):
    return generate_hash(f"{t}+{session['session_id']}")

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