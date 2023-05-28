from flask import g
try:
    from flask_babel import force_locale
except:
    pass

LANGUAGES = {
    "English": 'en',
    "Español": 'es'
}
    
def org_lang(f):

    def wrapper(*args, **kwargs):

        try:
            with force_locale(g.user.organization.lang):
                return f(*args, **kwargs)()
        except (RuntimeError, NameError) as e:
            return f(*args, **kwargs)()

    wrapper.__name__=f.__name__
    return wrapper