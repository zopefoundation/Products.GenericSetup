##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""

import unittest

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from Products.Five.component import enableSite
from Products.Five.component.interfaces import IObjectManagerSite
from zope.component import getGlobalSiteManager
from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.component import handle
from zope.component import queryAdapter
from zope.component import queryUtility
from zope.component import subscribers
from zope.component.globalregistry import base
from zope.component.hooks import clearSite
from zope.component.hooks import setHooks
from zope.component.hooks import setSite
from zope.interface import Interface
from zope.interface import implementer

from ..interfaces import IBody
from ..interfaces import IComponentsHandlerBlacklist
from ..testing import BodyAdapterTestCase
from ..testing import DummySetupEnviron
from ..testing import ExportImportZCMLLayer
from ..tests.common import DummyImportContext


try:
    from five.localsitemanager.registry import PersistentComponents
except ModuleNotFoundError:
    # Avoid generating a spurious dependency
    PersistentComponents = None


def createComponentRegistry(context):
    enableSite(context, iface=IObjectManagerSite)

    components = PersistentComponents('++etc++site')
    components.__bases__ = (base, )
    components.__parent__ = aq_base(context)
    # Make sure calls to getSiteManager on me return myself
    # necessary because OFS.ObjectManager.getSiteManager expects _components
    components._components = components
    context.setSiteManager(components)


class IDummyInterface(Interface):
    """A dummy interface."""

    def verify():
        """Returns True."""


class IDummyInterface2(Interface):
    """A second dummy interface."""

    def verify():
        """Returns True."""


@implementer(IDummyInterface)
class DummyUtility:
    """A dummy utility."""

    def verify(self):
        return True


class IAnotherDummy(Interface):
    """A third dummy interface."""

    def inc():
        """Increments handle count"""


class IAnotherDummy2(Interface):
    """A second dummy interface."""

    def verify():
        """Returns True."""


@implementer(IAnotherDummy)
class DummyObject:
    """A dummy object to pass to the handler."""

    handled = 0

    def inc(self):
        self.handled += 1


@implementer(IAnotherDummy2)
class DummyAdapter:
    """A dummy adapter."""

    def __init__(self, context):
        pass

    def verify(self):
        return True


def dummy_handler(context):
    """A dummy event handler."""

    context.inc()


@implementer(IDummyInterface)
class DummyTool(SimpleItem):
    """A dummy tool."""

    id = 'dummy_tool'
    meta_type = 'dummy tool'
    security = ClassSecurityInfo()

    @security.public
    def verify(self):
        return True


InitializeClass(DummyTool)


@implementer(IDummyInterface2)
class DummyTool2(SimpleItem):
    """A second dummy tool."""

    id = 'dummy_tool2'
    meta_type = 'dummy tool2'
    security = ClassSecurityInfo()

    @security.public
    def verify(self):
        return True


InitializeClass(DummyTool2)


@implementer(IComponentsHandlerBlacklist)
class DummyBlacklist:
    """A blacklist."""

    def getExcludedInterfaces(self):
        return (IDummyInterface, )


_COMPONENTS_BODY = b"""\
<?xml version="1.0" encoding="utf-8"?>
<componentregistry>
 <adapters>
  <adapter factory="Products.GenericSetup.tests.test_components.DummyAdapter"
     for="zope.interface.Interface"
     provides="Products.GenericSetup.tests.test_components.IAnotherDummy2"/>
  <adapter name="foo"
     factory="Products.GenericSetup.tests.test_components.DummyAdapter"
     for="zope.interface.Interface"
     provides="Products.GenericSetup.tests.test_components.IAnotherDummy2"/>
 </adapters>
 <subscribers>
  <subscriber
     factory="Products.GenericSetup.tests.test_components.DummyAdapter"
     for="Products.GenericSetup.tests.test_components.IAnotherDummy"
     provides="Products.GenericSetup.tests.test_components.IAnotherDummy2"/>
  <subscriber for="Products.GenericSetup.tests.test_components.IAnotherDummy"
     handler="Products.GenericSetup.tests.test_components.dummy_handler"/>
 </subscribers>
 <utilities>
  <utility factory="Products.GenericSetup.tests.test_components.DummyUtility"
     id="dummy_utility"
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

_REMOVE_IMPORT = b"""\
<?xml version="1.0" encoding="utf-8"?>
<componentregistry>
 <adapters>
  <adapter factory="Products.GenericSetup.tests.test_components.DummyAdapter"
     provides="Products.GenericSetup.tests.test_components.IAnotherDummy2"
     for="*" remove="True"/>
 </adapters>
 <subscribers>
  <subscriber
     factory="Products.GenericSetup.tests.test_components.DummyAdapter"
     for="Products.GenericSetup.tests.test_components.IAnotherDummy"
     provides="Products.GenericSetup.tests.test_components.IAnotherDummy2"
     remove="True"/>
  <subscriber
     for="Products.GenericSetup.tests.test_components.IAnotherDummy"
     handler="Products.GenericSetup.tests.test_components.dummy_handler"
     remove="True"/>
 </subscribers>
 <utilities>
  <utility id="dummy_utility"
     factory="Products.GenericSetup.tests.test_components.DummyUtility"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface"
     remove="True"/>
  <utility name="dummy tool name"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface"
     object="dummy_tool" remove="True"/>
  <utility name="foo"
     factory="Products.GenericSetup.tests.test_components.DummyUtility"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface2"
     remove="True"/>
 </utilities>
</componentregistry>
"""

_INTERFACE_COMPONENT = b"""\
<?xml version="1.0" encoding="utf-8"?>
<componentregistry>
 <adapters/>
 <subscribers/>
 <utilities>
  <utility name="test_interface"
     component="Products.GenericSetup.tests.test_components.ITestInterface"
     interface="Products.GenericSetup.tests.test_components.ITestInterfaceType"/>
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
        obj.registerAdapter(DummyAdapter, required=(None, ))
        obj.registerAdapter(DummyAdapter, required=(None, ), name='foo')

        obj.registerSubscriptionAdapter(DummyAdapter,
                                        required=(IAnotherDummy, ))
        obj.registerHandler(dummy_handler, required=(IAnotherDummy, ))

        util = DummyUtility()
        name = 'dummy_utility'
        util.__name__ = name
        util.__parent__ = aq_base(obj)
        obj._setObject(name,
                       aq_base(util),
                       set_owner=False,
                       suppress_events=True)
        obj.registerUtility(aq_base(obj[name]), IDummyInterface)

        util = DummyUtility()
        name = ('Products.GenericSetup.tests.test_components.'
                'IDummyInterface2-foo')
        util.__name__ = name
        util.__parent__ = aq_base(obj)
        obj._setObject(name,
                       aq_base(util),
                       set_owner=False,
                       suppress_events=True)
        obj.registerUtility(aq_base(obj[name]), IDummyInterface2, name='foo')

        tool = aq_base(obj.aq_parent['dummy_tool'])
        obj.registerUtility(tool, IDummyInterface, name='dummy tool name')

        tool2 = aq_base(obj.aq_parent['dummy_tool2'])
        obj.registerUtility(tool2, IDummyInterface2, name='dummy tool name2')

    def _verifyImport(self, obj):
        adapted = queryAdapter(object(), IAnotherDummy2)
        self.assertTrue(IAnotherDummy2.providedBy(adapted))
        self.assertTrue(adapted.verify())

        adapted = queryAdapter(object(), IAnotherDummy2, name='foo')
        self.assertTrue(IAnotherDummy2.providedBy(adapted))
        self.assertTrue(adapted.verify())

        dummy = DummyObject()
        results = [
            adap.verify() for adap in subscribers([dummy], IAnotherDummy2)
        ]
        self.assertEqual(results, [True])

        dummy = DummyObject()
        handle(dummy)
        self.assertEqual(dummy.handled, 1)

        util = queryUtility(IDummyInterface2, name='foo')
        self.assertTrue(IDummyInterface.providedBy(util))
        self.assertTrue(util.verify())
        self.assertEqual(util.__parent__, obj)
        name = ('Products.GenericSetup.tests.test_components.'
                'IDummyInterface2-foo')
        self.assertEqual(util.__name__, name)
        self.assertIn(name, obj.objectIds())

        util = queryUtility(IDummyInterface)
        self.assertTrue(IDummyInterface.providedBy(util))
        self.assertTrue(util.verify())
        self.assertEqual(util.__parent__, obj)
        name = 'dummy_utility'
        self.assertEqual(util.__name__, name)
        self.assertIn(name, obj.objectIds())

        util = queryUtility(IDummyInterface, name='dummy tool name')
        self.assertTrue(IDummyInterface.providedBy(util))
        self.assertTrue(util.verify())
        self.assertEqual(util.meta_type, 'dummy tool')

        # make sure we can get the tool by normal means
        tool = getattr(obj.aq_parent, 'dummy_tool')
        self.assertEqual(tool.meta_type, 'dummy tool')
        self.assertEqual(repr(aq_base(util)), repr(aq_base(tool)))

        util = queryUtility(IDummyInterface2, name='dummy tool name2')
        self.assertTrue(IDummyInterface2.providedBy(util))
        self.assertTrue(util.verify())
        self.assertEqual(util.meta_type, 'dummy tool2')

        # make sure we can get the tool by normal means
        tool = getattr(obj.aq_parent, 'dummy_tool2')
        self.assertEqual(tool.meta_type, 'dummy tool2')
        self.assertEqual(repr(aq_base(util)), repr(aq_base(tool)))

    def test_blacklist_get(self):
        obj = self._obj
        self._populate(obj)

        # Register our blacklist
        gsm = getGlobalSiteManager()
        gsm.registerUtility(DummyBlacklist(),
                            IComponentsHandlerBlacklist,
                            name='dummy')

        context = DummySetupEnviron()
        adapted = getMultiAdapter((obj, context), IBody)

        body = adapted.body
        self.assertNotIn(b'IComponentsHandlerBlacklist', body)
        self.assertNotIn(b'test_components.IDummyInterface"', body)

    def test_blacklist_set(self):
        obj = self._obj
        # Register our blacklist
        gsm = getGlobalSiteManager()
        gsm.registerUtility(DummyBlacklist(),
                            IComponentsHandlerBlacklist,
                            name='dummy')

        context = DummySetupEnviron()
        adapted = getMultiAdapter((obj, context), IBody)
        adapted.body = self._BODY

        util = queryUtility(IDummyInterface2, name='foo')
        self.assertTrue(IDummyInterface.providedBy(util))
        self.assertTrue(util.verify())
        util = queryUtility(IDummyInterface)
        self.assertIsNone(util)

        # now in update mode
        context._should_purge = False
        adapted = getMultiAdapter((obj, context), IBody)
        adapted.body = self._BODY

        util = queryUtility(IDummyInterface2, name='foo')
        self.assertTrue(IDummyInterface.providedBy(util))
        self.assertTrue(util.verify())
        util = queryUtility(IDummyInterface)
        self.assertIsNone(util)

        # and again in update mode
        adapted = getMultiAdapter((obj, context), IBody)
        adapted.body = self._BODY

        util = queryUtility(IDummyInterface2, name='foo')
        self.assertTrue(IDummyInterface.providedBy(util))
        self.assertTrue(util.verify())
        util = queryUtility(IDummyInterface)
        self.assertIsNone(util)

    def test_remove_components(self):
        from ..components import importComponentRegistry

        obj = self._obj
        self._populate(obj)
        self._verifyImport(obj)

        context = DummyImportContext(obj, False)
        context._files['componentregistry.xml'] = _REMOVE_IMPORT
        importComponentRegistry(context)

        adapted = queryAdapter(object(), IAnotherDummy2)
        self.assertIsNone(adapted)

        # This one should still exist
        adapted = queryAdapter(object(), IAnotherDummy2, name='foo')
        self.assertIsNotNone(adapted)

        dummy = DummyObject()
        results = [
            adap.verify() for adap in subscribers([dummy], IAnotherDummy2)
        ]
        self.assertEqual(results, [])

        dummy = DummyObject()
        handle(dummy)
        self.assertEqual(dummy.handled, 0)

        util = queryUtility(IDummyInterface2, name='foo')
        name = ('Products.GenericSetup.tests.test_components.'
                'IDummyInterface2-foo')
        self.assertIsNone(util)
        self.assertNotIn(name, obj.objectIds())

        util = queryUtility(IDummyInterface)
        self.assertIsNone(util)
        self.assertNotIn('dummy_utility', obj.objectIds())

        util = queryUtility(IDummyInterface, name='dummy tool name')
        self.assertIsNone(util)

        # This one should still exist
        util = queryUtility(IDummyInterface2, name='dummy tool name2')
        self.assertIsNotNone(util)

    def test_export_interface_component(self):
        sm = self._obj
        sm.registerUtility(ITestInterface, ITestInterfaceType,
                           "test_interface")
        context = DummySetupEnviron()
        adapted = getMultiAdapter((sm, context), IBody)
        body = adapted.body
        self.assertEqual(body, _INTERFACE_COMPONENT)

    def test_import_interface_component(self):
        from ..components import importComponentRegistry
        sm = self._obj
        context = DummyImportContext(sm, False)
        context._files['componentregistry.xml'] = _INTERFACE_COMPONENT
        importComponentRegistry(context)
        self.assertIs(
            sm.queryUtility(ITestInterfaceType, name="test_interface"),
            ITestInterface)

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
                              name='dummy')


class ITestInterface(Interface):
    """interface registered as utility."""


class ITestInterfaceType(Interface):
    """interface provided by ``ITestInterface``."""


if PersistentComponents is not None:

    def test_suite():
        # reimport to make sure tests are run from Products
        from ..tests.test_components import ComponentRegistryXMLAdapterTests

        return unittest.TestSuite(
            (unittest.defaultTestLoader.loadTestsFromTestCase(
                ComponentRegistryXMLAdapterTests), ))
else:

    def test_suite():
        return unittest.TestSuite()
