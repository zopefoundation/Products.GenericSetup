##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Component registry export / import support unit tests.

$Id$
"""

import unittest
import Testing

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Globals import InitializeClass
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from Products.Five.component import enableSite
from Products.Five.component.interfaces import IObjectManagerSite
from zope.app.component.hooks import setSite, clearSite, setHooks
from zope.component import getMultiAdapter
from zope.component import getGlobalSiteManager
from zope.component import getSiteManager
from zope.component import queryUtility
from zope.component.globalregistry import base
from zope.interface import implements
from zope.interface import Interface

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import IComponentsHandlerBlacklist
from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.testing import DummySetupEnviron
from Products.GenericSetup.testing import ExportImportZCMLLayer

try:
    from five.localsitemanager.registry import PersistentComponents
except ImportError:
    # Avoid generating a spurious dependency
    PersistentComponents = None

def createComponentRegistry(context):
    enableSite(context, iface=IObjectManagerSite)

    components = PersistentComponents()
    components.__bases__ = (base,)
    components.__parent__ = aq_base(context)
    context.setSiteManager(components)

class IDummyInterface(Interface):
    """A dummy interface."""

    def verify():
        """Returns True."""

class IDummyInterface2(Interface):
    """A second dummy interface."""

    def verify():
        """Returns True."""

class DummyUtility(object):
    """A dummy utility."""

    implements(IDummyInterface)

    def verify(self):
        return True


class DummyTool(SimpleItem):
    """A dummy tool."""
    implements(IDummyInterface)

    id = 'dummy_tool'
    meta_type = 'dummy tool'
    security = ClassSecurityInfo()

    security.declarePublic('verify')
    def verify(self):
        return True

InitializeClass(DummyTool)


class DummyTool2(SimpleItem):
    """A second dummy tool."""
    implements(IDummyInterface2)

    id = 'dummy_tool2'
    meta_type = 'dummy tool2'
    security = ClassSecurityInfo()

    security.declarePublic('verify')
    def verify(self):
        return True

InitializeClass(DummyTool2)


class DummyBlacklist(object):
    """A blacklist."""

    implements(IComponentsHandlerBlacklist)

    def getExcludedInterfaces(self):
        return (IDummyInterface, )


_COMPONENTS_BODY = """\
<?xml version="1.0"?>
<componentregistry>
 <adapters/>
 <utilities>
  <utility factory="Products.GenericSetup.tests.test_components.DummyUtility"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface"/>
  <utility name="dummy tool name"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface"
     object="dummy_tool"/>
  <utility name="dummy tool name2"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface2"
     object="dummy_tool2"/>
  <utility name="foo"
     factory="Products.GenericSetup.tests.test_components.DummyUtility"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface2"/>
 </utilities>
</componentregistry>
"""


class ComponentRegistryXMLAdapterTests(BodyAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from Products.GenericSetup.components import \
            ComponentRegistryXMLAdapter
        return ComponentRegistryXMLAdapter

    def _populate(self, obj):
        obj.registerUtility(DummyUtility(), IDummyInterface)
        obj.registerUtility(DummyUtility(), IDummyInterface2, name=u'foo')

        tool = aq_base(obj.aq_parent['dummy_tool'])
        obj.registerUtility(tool, IDummyInterface, name=u'dummy tool name')

        tool2 = aq_base(obj.aq_parent['dummy_tool2'])
        obj.registerUtility(tool2, IDummyInterface2, name=u'dummy tool name2')

    def _verifyImport(self, obj):
        util = queryUtility(IDummyInterface2, name=u'foo')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())

        util = queryUtility(IDummyInterface)
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())

        util = queryUtility(IDummyInterface, name='dummy tool name')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        self.assertEqual(util.meta_type, 'dummy tool')

        # make sure we can get the tool by normal means
        tool = getattr(obj.aq_parent, 'dummy_tool')
        self.assertEqual(tool.meta_type, 'dummy tool')
        self.assertEquals(repr(aq_base(util)), repr(aq_base(tool)))

        util = queryUtility(IDummyInterface2, name='dummy tool name2')
        self.failUnless(IDummyInterface2.providedBy(util))
        self.failUnless(util.verify())
        self.assertEqual(util.meta_type, 'dummy tool2')

        # make sure we can get the tool by normal means
        tool = getattr(obj.aq_parent, 'dummy_tool2')
        self.assertEqual(tool.meta_type, 'dummy tool2')
        self.assertEquals(repr(aq_base(util)), repr(aq_base(tool)))

    def test_blacklist_get(self):
        obj = self._obj
        self._populate(obj)

        # Register our blacklist
        gsm = getGlobalSiteManager()
        gsm.registerUtility(DummyBlacklist(),
                            IComponentsHandlerBlacklist,
                            name=u'dummy')

        context = DummySetupEnviron()
        adapted = getMultiAdapter((obj, context), IBody)

        body = adapted.body
        self.failIf('IComponentsHandlerBlacklist' in body)
        self.failIf('test_components.IDummyInterface"' in body)

    def test_blacklist_set(self):
        obj = self._obj
        # Register our blacklist
        gsm = getGlobalSiteManager()
        gsm.registerUtility(DummyBlacklist(),
                            IComponentsHandlerBlacklist,
                            name=u'dummy')

        context = DummySetupEnviron()
        adapted = getMultiAdapter((obj, context), IBody)
        adapted.body = self._BODY

        util = queryUtility(IDummyInterface2, name=u'foo')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        util = queryUtility(IDummyInterface)
        self.failUnless(util is None)

        # now in update mode
        context._should_purge = False
        adapted = getMultiAdapter((obj, context), IBody)
        adapted.body = self._BODY

        util = queryUtility(IDummyInterface2, name=u'foo')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        util = queryUtility(IDummyInterface)
        self.failUnless(util is None)

        # and again in update mode
        adapted = getMultiAdapter((obj, context), IBody)
        adapted.body = self._BODY

        util = queryUtility(IDummyInterface2, name=u'foo')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        util = queryUtility(IDummyInterface)
        self.failUnless(util is None)

    def setUp(self):
        # Create and enable a local component registry
        site = Folder()
        createComponentRegistry(site)
        setHooks()
        setSite(site)
        sm = getSiteManager()

        tool = DummyTool()
        site._setObject(tool.id, tool)

        tool2 = DummyTool2()
        site._setObject(tool2.id, tool2)

        self._obj = sm
        self._BODY = _COMPONENTS_BODY

    def tearDown(self):
        clearSite()
        # Make sure our global utility is gone again
        gsm = getGlobalSiteManager()
        gsm.unregisterUtility(provided=IComponentsHandlerBlacklist,
                              name=u'dummy')


if PersistentComponents is not None:
    def test_suite():
        # reimport to make sure tests are run from Products
        from Products.GenericSetup.tests.test_components \
                import ComponentRegistryXMLAdapterTests

        return unittest.TestSuite((
            unittest.makeSuite(ComponentRegistryXMLAdapterTests),
            ))
else:
    def test_suite():
        return unittest.TestSuite()

if __name__ == '__main__':
    from Products.GenericSetup.testing import run
    run(test_suite())
