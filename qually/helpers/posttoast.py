from flask import jsonify
from qually.__main__ import debug

def toast_redirect(target):
    return jsonify({"redirect": target}), 301

def toast_error(msg, status=409):
    return jsonify({"error": msg}), status

def toast(msg):
    return jsonify({"message": msg})
