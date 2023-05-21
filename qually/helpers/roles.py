try:
    from flask_babel import gettext as _
except:
    def _(x):
        return x

ROLES=[
    {
        "name": _("Document Control"),
        "value":"is_doc_control"
    },
    {
        "name": _("Material Review Board"),
        "value":"is_mrb"
    },
    {
        "name": _("Quality Management"),
        "value":"is_quality_management"
    }
]