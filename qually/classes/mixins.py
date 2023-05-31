from flask import request, g
import time
from sqlalchemy import Column, Integer, BigInteger, Float, String, Boolean, ForeignKey, Index, UniqueConstraint, text, or_, and_
from sqlalchemy.orm import deferred, relationship
try:
    from flask_babel import format_datetime
except ModuleNotFoundError:
    pass
import datetime

from qually.helpers.base36 import *
from qually.helpers.lazy import lazy

from qually.__main__ import app, Base

class core_mixin():

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

        return [x for x in self.approvals if x.status_id==phase]

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

                #other dropdown property, stored as int
                elif entry['kind']=='dropdown':
                    setattr(cls, entry['value'], Column(Integer, default=None))

        cls.owner=      relationship("User", primaryjoin=f"User.id=={cls.__name__}.owner_id")
        cls.logs=       relationship(f"{cls.__name__}Log", order_by=f"{cls.__name__}Log.id.desc()")
        cls.approvals=  relationship(f"{cls.__name__}Approval")
        

    @property
    def status(self):

        return self._lifecycle[self._status]['name']

    def can_edit(self, section):
        return g.user.has_seat and g.user in self._lifecycle[section]['users'] and (self._status == section or (self._status < section and self._lifecycle[section].get('early')=="edit"))