import requests

from qually.__main__ import app

def send_mail(to_address, subject, html, plaintext=None, files={}, from_address=f"{app.config['SITE_NAME']} <noreply@mail.{app.config['SERVER_NAME']}>"):

    if not app.config["MAILGUN_KEY"]:
        debug("Cannot send mail - no mailgun key")
        return


    url = f"https://api.mailgun.net/v3/mail.{app.config['SERVER_NAME']}/messages"

    data = {"from": from_address,
            "to": [to_address],
            "subject": subject,
            "text": plaintext,
            "html": html,
            }

    x= requests.post(
        url,
        auth=(
            "api", app.config["MAILGUN_KEY"]
            ),
        data=data,
        files=[("attachment", (k, files[k])) for k in files]
        )

   # debug([g.user.username, url, x.status_code, x.content])
    return x
