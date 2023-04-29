import PIL
from PIL import ImageFont, ImageDraw
from werkzeug.security import safe_join
from io import BytesIO

from qually.helpers.route_imports import *

@app.get("/icon/fontawesome/<style>/<icon>")
@app.get("/icon/fontawesome/<style>/<icon>/<color>")
@app.get("/icon/fontawesome/<style>/<icon>/<color>/<size>")
@cf_cache
def logo_fontawesome_icon(style, icon, color=None, size=500):

    size=int(size)

    if not color:
        color=app.config['COLOR_PRIMARY']

    primary_r=int(color[0:2], 16)
    primary_g=int(color[2:4], 16)
    primary_b=int(color[4:6], 16)

    primary = (primary_r, primary_g, primary_b, 255)

    base_layer = PIL.Image.new("RGBA", (size, size), color=primary)
    text_layer = PIL.Image.new("RGBA", (size, size), color=(255,255,255,0))

    filenames={
        'brands':'fa-brands-400',
        'light':'fa-light-300',
        'regular':'fa-regular-400',
        'sharp-regular':'fa-sharp-regular-400',
        'sharp-solid':'fa-sharp-solid-900',
        'solid':'fa-solid-900',
        'thin':'fa-thin-100'
    }
    if style not in filenames:
        abort(404)

    filename=filenames[style]

    font = ImageFont.truetype(
        f"{app.config['RUQQUSPATH']}/assets/fontawesome/webfonts/{filename}.ttf", 
        size=size * 3 // 5
        )

    icon=icon[0]

    box=font.getbbox(icon)

    d = ImageDraw.Draw(text_layer)
    d.text(
        (
            size // 2 - box[2] // 2 + 1, 
            size // 2 - (box[3]+box[1]) // 2 + 1
            ),
        icon, 
        font=font,
        fill=(255,255,255,255)
        )

    output=PIL.Image.alpha_composite(base_layer, text_layer)

    bytesout=BytesIO()
    output.save(bytesout, format="PNG")
    bytesout.seek(0)
    return send_file(bytesout, mimetype="image/png")

# @app.get("/apple-touch-icon.png")
# @app.get("/apple-touch-icon-precomposed.png")
# @app.get("/apple-touch-icon-<width>x<height>-precomposed.png")
# @app.get("/apple-touch-icon-<width>x<height>.png")
# @cf_cache
# def get_apple_touch_icon_sized_png(width=192, height=192):

#     width=int(width)
#     height=int(height)
#     return get_assets_images_splash('splash', width, height)
