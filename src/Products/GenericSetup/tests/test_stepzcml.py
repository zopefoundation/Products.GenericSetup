##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Unit tests for import/export step zcml module.
"""

import unittest

from Zope2.App import zcml
from zope.testing.cleanup import cleanUp

import Products.GenericSetup

from ..registry import _import_step_registry


EMPTY_ZCML = '''\
<configure xmlns:genericsetup="http://namespaces.zope.org/genericsetup">
</configure>'''

ONE_STEP_ZCML = '''\
<configure xmlns:genericsetup="http://namespaces.zope.org/genericsetup"
           i18n_domain="genericsetup">
<genericsetup:importStep
    name="Products.GenericSetup.teststep"
    title="step title"
    description="step description"
    handler="Products.GenericSetup.initialize"
    />
</configure>'''


class ImportStepTests(unittest.TestCase):

    def setUp(self):
        zcml.load_config('meta.zcml', Products.GenericSetup)

    def tearDown(self):
        cleanUp()

    def testEmptyImport(self):
        zcml.load_string(EMPTY_ZCML)
        self.assertEqual(len(_import_step_registry.listSteps()), 0)

    def testOneStepImport(self):
        zcml.load_string(ONE_STEP_ZCML)
        self.assertEqual(_import_step_registry.listSteps(),
                         ['Products.GenericSetup.teststep'])
        info = _import_step_registry.getStepMetadata(
            'Products.GenericSetup.teststep')
        self.assertEqual(info['description'],
                         'step description')
        self.assertEqual(info['title'],
                         'step title')
        self.assertEqual(info['handler'],
                         'Products.GenericSetup.initialize')
        self.assertEqual(info['id'],
                         'Products.GenericSetup.teststep')


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(ImportStepTests),
    ))
