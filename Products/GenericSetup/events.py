from zope.interface import implements
from Products.GenericSetup.interfaces import IBeforeProfileImportEvent
from Products.GenericSetup.interfaces import IProfileImportedEvent

class BaseProfileImportEvent(object):
    def __init__(self, tool, profile_id, steps, full_import):
        self.tool=tool
        self.profile_id=profile_id
        self.steps=steps
        self.full_import=full_import


class BeforeProfileImportEvent(BaseProfileImportEvent):
    implements(IBeforeProfileImportEvent)


class ProfileImportedEvent(BaseProfileImportEvent):
    implements(IProfileImportedEvent)
