from .capa import CAPA, CAPAApproval, CAPALog
from .deviation import Deviation, DeviationApproval, DeviationLog
from .file import File
from .item import Item, ItemRevision
from .ncmr import NCMR, NCMRApproval, NCMRLog
from .organization import Organization, OrganizationAuditLog
from .paypal import PayPalClient, PayPalTxn
from .user import User

ALL_PROCESSES={
    x._name.lower(): x for x in [CAPA, Deviation, NCMR]
}