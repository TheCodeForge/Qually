from flask import jsonify
import json
import urllib
from .security import generate_hash, validate_hash
from qually.__main__ import debug

def toast_redirect(target):
    return jsonify({"redirect": target}), 301

def toast_error(msg, status=409):
    return jsonify({"error": msg}), status

def toast(msg):
    return jsonify({"message": msg})
    
def tokenify(path, data, token=None):
    
    data.pop("token", None)
    
    string=f"{path}?{urllib.parse.urlencode(data)}"
    
    if token:
        data['token']= validate_hash(string, token)
        return f"{path}?{urllib.parse.urlencode(data)}"
    else:
        return generate_hash(string)
