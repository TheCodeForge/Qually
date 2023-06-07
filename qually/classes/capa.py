from qually.helpers.class_imports import *
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    def _(x):
        return x

class CAPA(Base, core_mixin, process_mixin):

    __tablename__="capa"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    number=Column(Integer, default=0, index=True)
    _status = Column(Integer, default=0)

    _name="CAPA"

    __table_args__=(
            UniqueConstraint(
                'number', 
                'organization_id',
                name=f'capa_org_number_unique'
                ),
            )

    organization=relationship("Organization")

    @classmethod
    def name_readable(cls):
        return _("Corrective and Preventive Action")

    @classmethod
    def _assignment_query_args(cls):

        args= [
            and_(
                CAPA._status==0, 
                CAPA.owner_id==g.user.id
                ),
            and_(
                CAPA._status==2, 
                CAPA.root_cause_investigator_id==g.user.id
                ),
            and_(
                CAPA._status.in_([4, 5]), 
                CAPA.action_assignee_id==g.user.id
                )
            ]

        if g.user.is_quality_management:
            args.append(CAPA._status.in_([1,3,6]))

        return args

    @property
    def _lifecycle(self):
        return {
            0: {
                'name': _("New"),
                'users': [self.owner],
                'files': True
                },
            1: {
                'name': _("Initial Review"),
                'users': self.organization.quality_mgmt_users
                },
            2: {
                'name': _("Investigation"),
                'users': [self.root_cause_investigator],
                'files': True
                },
            3: {
                'name': _("Approval to Implement"),
                'users': self.organization.quality_mgmt_users
                },
            4: {
                'name': _("Implementation"),
                'users': [self.action_assignee],
                'files': True
                },
            5: {
                'name': _("Verification of Effectiveness"),
                'users': [self.action_assignee],
                'files': True
                },
            6: {
                'name': _("Final Review"),
                'users': self.organization.quality_mgmt_users
                },
            100: {
                'name': _("Closed"),
                'users': []
                },
            101: {
                'name': _("Terminated"),
                'users': []
                }
        }

    @classmethod
    @org_lang
    def _sources(cls):

        return {
                1: _("Service request"),
                2: _("Internal audit finding"),
                3: _("External audit finding"),
                4: _("Quality Assurance inspection"),
                5: _("General observation"),
                6: _("Risk assessment"),
                7: _("Management review"),
                8: _("Failure analysis")
            }

    @classmethod
    def _layout(cls):
        return {
            0:[
                {
                    "name":_("Issue Source"),
                    "value":"issue_source",
                    "kind": "dropdown",
                    "values": cls._sources()
                },
                {
                    "name":_("Describe Issue"),
                    "value":"describe_issue",
                    "kind": "multi",
                    "help": _("Include a reference to the particular regulation, SOP, or other standard that is not being complied with.")
                },
                {
                    "name":_("Who discovered issue?"),
                    "value":"discoverer",
                    "kind": "user"
                },
                {
                    "name":_("How was issue discovered?"),
                    "value":"how_discovered",
                    "kind": "multi"
                },
                {
                    "name":_("Description of Non-Conformance"),
                    "value":"nc_description",
                    "kind": "multi",
                    "help":_("Identify the specification or requirement to which the material fails to conform.")
                },
                {
                    "name":_("Immediate Actions"),
                    "value":"new_comments",
                    "kind": "multi",
                    "help":_("Describe any immediate corrections that were taken, such as quarantining nonconforming product.")
                }
            ],
            1: [
                {
                    "name":_("Root Cause Investigator"),
                    "value":"root_cause_investigator",
                    "kind": "user",
                    "help": _("Assign someone to investigate this issue.")
                }
            ],
            2: [
                {
                    "name":_("Root Cause Analysis"),
                    "value":"root_cause_analysis",
                    "kind": "multi",
                    "help": _("Describe the root cause investigation analysis and conclusions. Use investigative techniques such as 5-Whys, fault-tree analysis, or fishbone analysis.")
                },
                {
                    "name":_("Scope and Impact"),
                    "value":"scope_and_impact",
                    "kind":"multi",
                    "help":_("Identify the bracketing boundaries of the problem. How extensive is the impact?")
                },
                {
                    "name":_("Risk assessment"),
                    "value":"risk_assessment",
                    "kind":"multi",
                    "help":_("Identify and evaluate potential risks to the patient, to the process, and to compliance.")
                },
                {
                    "name":_("Action Plan"),
                    "value":"action_plan",
                    "kind":"multi",
                    "help":_("Describe the actions to remedy the issue's root cause.")
                },
                {
                    "name":_("Verification of Effectiveness Plan"),
                    "value":"voe_plan",
                    "kind":"multi",
                    "help":_("How will the effectiveness of the action plan be measured and evaluated?")
                }
            ],
            3: [
                {
                    "name":_("Implementation Assignee"),
                    "value":"action_assignee",
                    "kind": "user",
                    "help": _("Assign someone to execute the action plan.")
                }
            ],
            4: [
                {
                    "name":_("Actions taken"),
                    "value":"actions_taken",
                    "kind":"multi",
                    "help":_("Describe actions performed. These should reflect the approved plan.")
                }
            ],
            5: [
                {
                    "name":_("Verification of Effectiveness"),
                    "value":"voe_executed",
                    "kind":"multi",
                    "help":_("Measure and evaluate the effectiveness of the actions performed, following the approved Verification of Effectiveness plan.")
                }
            ],
            6: []
        }
    
    @property
    @lazy
    def _transitions(self):

        return {
            0: [
                {
                    "id":"submit",
                    "to": 1,
                    "name": _("Submit"),
                    "description": _("Submit this record to Quality Assurance for review."),
                    "color": "success",
                    "users": [self.owner],
                    "approval":True
                },
                {
                    "id":"terminate",
                    "to": 101,
                    "name": _("Terminate"),
                    "description": _("Permanently archive this record. This cannot be undone."),
                    "color": "danger",
                    "users": [self.owner]
                }
            ],
            1: [
                {
                    "id":"reject",
                    "to": 0,
                    "name": _("Reject"),
                    "description": _("Send this record back to its initiator for revision."),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "secondary",
                    "comments": True,
                },
                {
                    "id":"withdraw",
                    "to": 0,
                    "name": _("Withdraw"),
                    "users": [self.owner],
                    "color": "secondary"
                },
                {
                    "id":"advance",
                    "to": 2,
                    "name": _("Approve"),
                    "description": _("Send this record to the Material Review Board."),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "success",
                    "approval":True
                },
                {
                    "id":"terminate",
                    "to": 101,
                    "name": _("Terminate"),
                    "description": _("Permanently archive this record. This cannot be undone."),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "danger"
                }
            ],
            2: [
                {
                    "id":"submit",
                    "to":3,
                    "name": _("Submit"),
                    "description": _("Submit investigative results to quality management."),
                    "users": [self.root_cause_investigator],
                    "color": "success",
                    "approval":True
                }
            ],
            3: [
                {
                    "id":"reject",
                    "to": 0,
                    "name": _("Reject"),
                    "description": _("Send this record back to its initiator for revision."),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "secondary",
                    "comments": True,
                },
                {
                    "id":"withdraw",
                    "to": 0,
                    "name": _("Withdraw"),
                    "users": [self.owner],
                    "color": "secondary"
                },
                {
                    "id":"advance",
                    "to": 4,
                    "name": _("Approve"),
                    "description": _("Advance to implementation."),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "success",
                    "approval":True
                }
            ],
            4: [
                {
                    "id":"continue",
                    "to": 5,
                    "name": _("Continue to Verification of Effectiveness"),
                    "description":_("Continue to Verification of Effectiveness."),
                    "users": [self.action_assignee],
                    "color": "success"
                }
            ],
            5: [
                {
                    "id":"submit",
                    "to": 6,
                    "name": _("Submit"),
                    "description":_("Submit to Final Review"),
                    "users": [self.action_assignee],
                    "color": "success",
                    "approval":True
                },
                {
                    "id":"return",
                    "to": 4,
                    "name": _("Return to Implementation"),
                    "description":_("Return to Implementation"),
                    "users": [self.action_assignee],
                    "color": "secondary"
                }
            ],
            6: [
                {
                    "id":"approve",
                    "to": 100,
                    "name": _("Approve and Close"),
                    "description":_("Approve and close"),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "success",
                    "approval":True
                },
                {
                    "id":"reject",
                    "to": 5,
                    "name": _("Reject to Verification of Effectiveness"),
                    "description":_("Reject to Verification of Effectiveness"),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "warning"
                }
            ]
        }

CAPA._cols()
    
class CAPAApproval(Base, core_mixin):

    __tablename__="capa_approval"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("capa.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    status_id=Column(Integer)
    created_utc=Column(Integer)

    user=relationship("User", lazy="joined", innerjoin=True)


class CAPALog(Base, core_mixin):

    __tablename__="capa_audit"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("capa.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    created_ip=Column(String(64))

    key=Column(String)
    value=Column(String)

    user=relationship("User", lazy="joined", innerjoin=True)
