from flask import jsonify
from qually.__main__ import debug
from qually.classes.errors import ToastError

def toast_redirect(target):
    return jsonify({"redirect": target}), 301

def toast_error(msg, status=409):
    raise ToastError(msg, code=status)

def toast(msg, data={}):
    output={"message": msg}
    output.update(data)
    return jsonify(output)


