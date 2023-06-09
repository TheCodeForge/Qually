from flask import request, g
import time
from sqlalchemy import Column, Integer, BigInteger, Float, String, Boolean, ForeignKey, Index, UniqueConstraint, text, or_, and_
from sqlalchemy.orm import deferred, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList

try:
    from flask_babel import format_datetime, force_locale, gettext as _
except ModuleNotFoundError:
    pass
import datetime

from qually.helpers.base36 import *
from qually.helpers.lazy import lazy
from qually.helpers.sanitize import txt, html
from qually.helpers.posttoast import *

from qually.__main__ import app, Base

class core_mixin():

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

    @property
    @lazy
    def base36id(self):

        return base36encode(self.id)

    @property
    @lazy
    def permalink_full(self):
        return f"http{'s' if app.config['HTTPS'] else ''}://{app.config['SERVER_NAME']}{self.permalink}"

    @property
    @lazy
    def age(self):
        return g.time - self.created_utc

    @property
    @lazy
    def created_date(self):
        return format_datetime(datetime.datetime.fromtimestamp(self.created_utc), "dd MMMM yyyy")

    @property
    @lazy
    def created_datetime(self):
        return format_datetime(datetime.datetime.fromtimestamp(self.created_utc), "dd MMMM yyyy HH:mm")

class process_mixin():

    @property
    def name(self):
        return f"{getattr(g.user.organization, f'{self._name.lower()}_prefix')}-{self.number:0>5}"

    @property
    def permalink(self):
        return f"/{self.name}"
    
    @property
    @lazy
    def available_transitions(self):

        tsns=self._transitions.get(self._status, {})

        return [x for x in tsns if tsns]

    def phase_approvals(self, phase):

        return [x for x in getattr(self, "approvals", []) if x.status_id==phase]

    @property
    def has_approved(self):

        return g.user.id in [x.user_id for x in self.phase_approvals(self._status)]

    @classmethod
    def _cols(cls):

        #set columns that all processes need

        cls.created_utc=Column(Integer)

        #Iterate through process template to create db columns for data captured in process
        data=cls._layout()

        #for each phase in the template...
        for status in data:

            #Due date property
            setattr(cls, f"phase_{status}_due_utc", Column(BigInteger))

            #for each field...
            for entry in data[status]:

                # if not entry.get("column",True):
                #     continue

                #single line text - safe html only
                if entry['kind']=='text':
                    setattr(cls, entry['value'], Column(String, default=''))

                #multi line text - raw and safe properties
                elif entry['kind']=='multi':
                    setattr(cls, entry['value'], Column(String, default=''))
                    setattr(cls, f"{entry['value']}_raw", Column(String, default=''))

                #user selection property
                elif entry['kind']=='user':
                    setattr(cls, f"{entry['value']}_id", Column(Integer, ForeignKey("users.id")))
                    setattr(cls, entry['value'], relationship("User", primaryjoin=f"User.id=={cls.__name__}.{entry['value']}_id"))

                # elif entry['kind']=='user_multi':
                #     setattr(cls, f"{entry['value']}_ids", Column(MutableList.as_mutable(ARRAY(Integer)), ForeignKey("users.id")))

                #other dropdown property, stored as int
                elif entry['kind']=='dropdown':
                    setattr(cls, entry['value'], Column(Integer, default=None))

                elif entry['kind']=='int':
                    setattr(cls, entry['value'], Column(Integer, default=None))

                else:
                    raise ValueError(f"unknown template data type {entry['kind']}")

        cls.owner=      relationship("User", primaryjoin=f"User.id=={cls.__name__}.owner_id")
        cls.logs=       relationship(f"{cls.__name__}Log", order_by=f"{cls.__name__}Log.id.desc()")
        cls.approvals=  relationship(f"{cls.__name__}Approval")

    @classmethod
    def _next_number(cls):
        return g.user.organization.next_id(cls._name.lower())
        

    @property
    def status(self):

        return self._lifecycle[self._status]['name']

    def can_edit(self, section):
        return g.user.has_seat and g.user in self._lifecycle[section]['users'] and (self._status == section or (self._status < section and self._lifecycle[section].get('early')=="edit"))

    def _after_create(self):
        pass

    def _edit_form(self):


        key=None
        for phase in self._lifecycle:

            if not self.can_edit(phase):
                continue

            source=self._lifecycle[phase].get("object_data", self)

            for entry in self._layout()[phase]:


                if entry['value'] in request.form and (source==self or source.__repr__()==request.form.get("data_obj")):

                    if entry.get('readonly'):
                        return toast_error(_("Property {x} is read-only").format(x=entry['name']), 403)


                    if entry['kind']=='multi':
                        setattr(source, f"{entry['value']}_raw", request.form[entry['value']])
                        setattr(source, entry['value'], html(request.form[entry['value']]))
                        key=entry['name']
                        value=txt(request.form[entry['value']])
                        response=getattr(source, entry['value']) or "<p></p>"
                    elif entry['kind']=='dropdown':

                        if int(request.form[entry['value']]) not in entry['values']:
                            return toast_error(_("Invalid selection for {x}").format(x=entry['name']))

                        setattr(source, entry['value'], int(request.form[entry['value']]))
                        key=entry['name']
                        value=entry['values'].get(int(request.form[entry['value']]))
                        response=value
                    elif entry['kind']=='user':
                        n=request.form.get(entry['value'])
                        if n:
                            if not g.user.organization.users.filter_by(id=int(n)).first():
                                return toast_error(_("Invalid user"))
                            setattr(source, f"{entry['value']}_id", int(n))
                            g.db.add(source)
                            g.db.flush()
                            g.db.refresh(source)
                            value=getattr(source, entry['value']).name
                            response=f'<a href="{getattr(source, entry["value"]).permalink}">{getattr(source, entry["value"]).name}</a>'
                        else:
                            setattr(source, entry['value'], None)
                            response="<p></p>"
                            value=""
                        key=entry['name']
                    elif entry['kind']=='int':
                        setattr(source, entry['value'], int(request.form[entry['value']]))
                        key=entry['name']
                        value=getattr(source, entry['value'])
                        response=value
                    else:
                        setattr(source, entry['value'], txt(request.form[entry['value']]))
                        key=entry['name']
                        value=getattr(source, entry['value'])
                        response=value

                    
                    g.db.add(source)
                    if source != self:
                        key= f"{source.name} / {key}"
                    break

            if key!=None:
                break

        if key==None:
            return None, None, None, None


        return key, value, response, entry.get("reload", False)

    def modify_layout(self):
        #Override this to customize the record display based on custom data
        # layout=self._layout()
        # lifecycle=self._lifecycle
        # modify layout
        # modify lifecycle
        # self.__dict__["_layout"]=lambda:layout
        # self.__dict__["_lifecycle"]=lifecycle

        #At the same time, adjust _lifecycle as follows
        # @property
        # def _lifecycle(self)
        #     return self.__dict__.get("_lifecycle") or {.....}
        pass

    def _after_phase_change(self):
        pass

class revisioned_process_mixin(process_mixin):

    @property
    @lazy
    def effective_revision(self):
        return self.revisions.filter_by(_status=1).first()

    @property
    def display_revision(self):
        set_display= self.__dict__.get("display_revision")

        if set_display:
            print(f"found set display revision {set_display}")
            return set_display
        else:
            print("using effective revision")
            return self.effective_revision

    @property
    def history_revisions(self):
        return self.revisions.filter_by(self._revision_class.revision_number != None).order_by(self._revision_class.revision_number.desc()).all()