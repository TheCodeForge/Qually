from hmac import new as hmac_new, compare_digest as hmac_compare_digest
from werkzeug.security import generate_password_hash
from os import environ
import time
import random

from .base36 import base36encode, base36decode

from qually.__main__ import app

def generate_hash(string):

    msg = bytes(string, "utf-16")

    return hmac_new(key=bytes(app.config["SECRET_KEY"], "utf-16"),
                    msg=msg,
                    digestmod='sha256'
                    ).hexdigest()


def validate_hash(string, hashstr):

    return hmac_compare_digest(hashstr, generate_hash(string))


def hash_password(password):

    return generate_password_hash(
        password, 
        method='pbkdf2:sha512', 
        salt_length=8)

def safe_compare(x, y):
    
    before=time.time()
    
    returnval=(x==y)
    
    after=time.time()
    
    time.sleep(random.uniform(0.0, 0.1)-(after-before))
    
    return returnval

def otp_recovery_code(user, otp_secret):

    hashstr = generate_hash(f"{otp_secret}+{user.id}")

    removal_code = base36encode(int(hashstr,16))
    
    while len(removal_code)<25:
        removal_code="0"+removal_code

    return removal_code.upper()