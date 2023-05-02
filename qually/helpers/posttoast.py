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
    
def tokenify(string):
    
    try:
        path, querystring = string.split('?')
    except ValueError:
        path=string
        querystring=""
    
    args={}
    for pair in querystring.split('&'):
        if not pair:
            break
        key, value=pair.split('=')
        args[key]=value
        
    args['_path']=path

    string=json.dumps(args, sort_keys=True)

    debug(string)
    
    token=generate_hash(json.dumps(args, sort_keys=True))
    
    if querystring:
        return f"{string}&token={token}"
    else:
        return f"{string}?token={token}"
