##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Base classes for testing interface conformance.

Derived testcase classes should define '_getTargetClass()', which must
return the class being tested for conformance.
"""


class ConformsToISetupContext:

    def test_ISetupContext_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import ISetupContext

        verifyClass(ISetupContext, self._getTargetClass())


class ConformsToIImportContext:

    def test_IImportContext_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IImportContext

        verifyClass(IImportContext, self._getTargetClass())


class ConformsToIExportContext:

    def test_IExportContext_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IExportContext

        verifyClass(IExportContext, self._getTargetClass())


class ConformsToIChunkableExportContext:

    def test_IChunkableExportContext_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IChunkableExportContext

        verifyClass(IChunkableExportContext, self._getTargetClass())


class ConformsToIChunkableImportContext:

    def test_IChunkableImportContext_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IChunkableImportContext

        verifyClass(IChunkableImportContext, self._getTargetClass())


class ConformsToIStepRegistry:

    def test_IStepRegistry_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IStepRegistry

        verifyClass(IStepRegistry, self._getTargetClass())


class ConformsToIImportStepRegistry:

    def test_IImportStepRegistry_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IImportStepRegistry

        verifyClass(IImportStepRegistry, self._getTargetClass())


class ConformsToIExportStepRegistry:

    def test_IExportStepRegistry_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IExportStepRegistry

        verifyClass(IExportStepRegistry, self._getTargetClass())


class ConformsToIToolsetRegistry:

    def test_IToolsetRegistry_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IToolsetRegistry

        verifyClass(IToolsetRegistry, self._getTargetClass())


class ConformsToIProfileRegistry:

    def test_IProfileRegistry_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IProfileRegistry

        verifyClass(IProfileRegistry, self._getTargetClass())


class ConformsToISetupTool:

    def test_ISetupTool_conformance(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import ISetupTool

        verifyClass(ISetupTool, self._getTargetClass())


class ConformsToIContentFactory:

    def test_conforms_to_IContentFactory(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IContentFactory

        verifyClass(IContentFactory, self._getTargetClass())


class ConformsToIContentFactoryName:

    def test_conforms_to_IContentFactory(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IContentFactoryName

        verifyClass(IContentFactoryName, self._getTargetClass())


class ConformsToIFilesystemExporter:

    def test_conforms_to_IFilesystemExporter(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IFilesystemExporter

        verifyClass(IFilesystemExporter, self._getTargetClass())


class ConformsToIFilesystemImporter:

    def test_conforms_to_IFilesystemImporter(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IFilesystemImporter

        verifyClass(IFilesystemImporter, self._getTargetClass())


class ConformsToIINIAware:

    def test_conforms_to_IINIAware(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IINIAware

        verifyClass(IINIAware, self._getTargetClass())


class ConformsToICSVAware:

    def test_conforms_to_ICSVAware(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import ICSVAware

        verifyClass(ICSVAware, self._getTargetClass())


class ConformsToIDAVAware:

    def test_conforms_to_IDAVAware(self):

        from zope.interface.verify import verifyClass

        from ..interfaces import IDAVAware

        verifyClass(IDAVAware, self._getTargetClass())
