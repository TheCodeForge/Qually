from flask import jsonify
import json
import urllib
from .security import generate_hash
from qually.__main__ import debug

def toast_redirect(target):
    return jsonify({"redirect": target}), 301

def toast_error(msg, status=409):
    return jsonify({"error": msg}), status

def toast(msg):
    return jsonify({"message": msg})
    
def tokenify(path, data):
    

    data.pop('token',None)
    data['_path']=path
    
    argstring=json.dumps(args, sort_keys=True)

    debug(argstring)
    
    token=generate_hash(argstring)
    
    if querystring:
        return f"{string}&token={token}"
    else:
        return f"{string}?token={token}"
