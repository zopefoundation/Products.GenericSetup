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
from Testing.ZopeTestCase import ZopeTestCase

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem

from Products.Five.component import enableSite
from Products.Five.component.interfaces import IObjectManagerSite
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.testing import ExportImportZCMLLayer
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from zope.app.component.hooks import setSite, clearSite, setHooks
from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.component import queryUtility
from zope.component.globalregistry import base
from zope.interface import implements
from zope.interface import Interface

try:
    from five.localsitemanager.registry import PersistentComponents
except ImportError:
    # Avoid generating a spurious dependency
    PersistentComponents = None

_marker = []

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
    implements(IDummyInterface)

    id = 'dummy_tool2'
    meta_type = 'dummy tool2'
    security = ClassSecurityInfo()

    security.declarePublic('verify')
    def verify(self):
        return True

InitializeClass(DummyTool2)


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
     interface="Products.GenericSetup.tests.test_components.IDummyInterface"
     object="dummy_tool2"/>
  <utility name="foo"
     factory="Products.GenericSetup.tests.test_components.DummyUtility"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface"/>
 </utilities>
</componentregistry>
"""


class ComponentRegistryXMLAdapterTests(ZopeTestCase, BodyAdapterTestCase):

    layer = ExportImportZCMLLayer

    def _populate(self, obj):
        obj.registerUtility(DummyUtility(), IDummyInterface)
        obj.registerUtility(DummyUtility(), IDummyInterface, name=u'foo')

        tool = aq_base(self.app['dummy_tool'])
        obj.registerUtility(tool, IDummyInterface, name=u'dummy tool name')

        tool2 = aq_base(self.app['dummy_tool2'])
        obj.registerUtility(tool2, IDummyInterface, name=u'dummy tool name2')

    def test_body_get(self):
        self._populate(self._obj)
        context = DummyExportContext(self.app)
        adapted = getMultiAdapter((self._obj, context), IBody)
        self.assertEqual(adapted.body, self._BODY)

    def test_body_set(self):
        context = DummyImportContext(self.app)
        adapted = getMultiAdapter((self._obj, context), IBody)
        adapted.body = self._BODY
        self._verifyImport(self._obj)
        self.assertEqual(adapted.body, self._BODY)

        # now in update mode
        context._should_purge = False
        adapted = getMultiAdapter((self._obj, context), IBody)
        adapted.body = self._BODY
        self._verifyImport(self._obj)
        self.assertEqual(adapted.body, self._BODY)

        # and again in update mode
        adapted = getMultiAdapter((self._obj, context), IBody)
        adapted.body = self._BODY
        self._verifyImport(self._obj)
        self.assertEqual(adapted.body, self._BODY)

    def _getTargetClass(self):
        from Products.GenericSetup.components import \
            ComponentRegistryXMLAdapter
        return ComponentRegistryXMLAdapter

    def _verifyImport(self, obj):
        util = queryUtility(IDummyInterface, name=u'foo')
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
        tool = getattr(self.app, 'dummy_tool')
        self.assertEqual(tool.meta_type, 'dummy tool')
        self.assertEquals(repr(aq_base(util)), repr(aq_base(tool)))

        util = queryUtility(IDummyInterface, name='dummy tool name2')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        self.assertEqual(util.meta_type, 'dummy tool2')

        # make sure we can get the tool by normal means
        tool = getattr(self.folder, 'dummy_tool2')
        self.assertEqual(tool.meta_type, 'dummy tool2')
        self.assertEquals(repr(aq_base(util)), repr(aq_base(tool)))

    def afterSetUp(self):
        BodyAdapterTestCase.setUp(self)

        # Create and enable a local component registry
        createComponentRegistry(self.app)
        setHooks()
        setSite(self.app)
        sm = getSiteManager()

        tool = DummyTool()
        self.app._setObject(tool.id, tool)

        tool2 = DummyTool2()
        self.app._setObject(tool2.id, tool2)

        self._obj = sm
        self._BODY = _COMPONENTS_BODY

    def beforeTearDown(self):
        clearSite()

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
