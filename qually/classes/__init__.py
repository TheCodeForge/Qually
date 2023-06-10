from .approver_groups import ChangeApproverGroup, ChangeApproverGroupRelationship
from .capa import CAPA, CAPAApproval, CAPALog
from .changeorder import ChangeOrder, ChangeOrderApproval, ChangeOrderLog
from .deviation import Deviation, DeviationApproval, DeviationLog
from .file import File
from .item import Item, ItemLog, ItemRelationship, ItemRevision
from .ncmr import NCMR, NCMRApproval, NCMRLog
from .organization import Organization, OrganizationAuditLog
from .paypal import PayPalClient, PayPalTxn
from .user import User

ALL_PROCESSES={
    x._name.lower(): x for x in [CAPA, ChangeOrder, Deviation, NCMR, Item]
}