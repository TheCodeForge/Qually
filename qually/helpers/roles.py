try:
    from flask_babel import gettext as _
except:
    def _(x):
        return x

ROLES=[
    {
        "name": _("Document Control"),
        "value":"is_doc_control",
        "rel":"doc_control_users"
    },
    {
        "name": _("Material Review Board"),
        "value":"is_mrb",
        "rel":"mrb_users"
    },
    {
        "name": _("Quality Management"),
        "value":"is_quality_management",
        "rel":"quality_mgmt_users"
    }
]