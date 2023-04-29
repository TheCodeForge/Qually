from flask import jsonify

def toast_redirect(target):
    return jsonify({"redirect": target}), 301

def toast_error(msg, status=400):
    return jsonify({"error": msg}), status

def toast(msg):
    return jsonify({"message": msg})