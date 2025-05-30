##############################################################################
#
# Copyright (c) 2006-2007 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""GenericSetup ZCML directives.
"""

import zope.schema
from zope.configuration.fields import GlobalObject
from zope.configuration.fields import MessageID
from zope.configuration.fields import Path
from zope.configuration.fields import Tokens
from zope.interface import Interface

from .interfaces import BASE
from .registry import _export_step_registry
from .registry import _import_step_registry
from .registry import _profile_registry
from .upgrade import UpgradeDepends
from .upgrade import UpgradeStep
from .upgrade import _registerNestedUpgradeStep
from .upgrade import _registerUpgradeStep
from .utils import _getHash


# genericsetup:registerProfile


class IRegisterProfileDirective(Interface):

    """Register profiles with the global registry.
    """

    name = zope.schema.TextLine(
        title='Name',
        description="If not specified 'default' is used.",
        default='default',
        required=False)

    title = MessageID(
        title='Title',
        description='Optional title for the profile.',
        default=None,
        required=False)

    description = MessageID(
        title='Description',
        description='Optional description for the profile.',
        default=None,
        required=False)

    directory = Path(
        title='Path',
        description="If not specified 'profiles/<name>' is used.",
        required=False)

    provides = GlobalObject(
        title='Type',
        description="If not specified 'BASE' is used.",
        default=BASE,
        required=False)

    for_ = GlobalObject(
        title='Site Interface',
        description='If not specified the profile is always available.',
        default=None,
        required=False)

    pre_handler = GlobalObject(
        title='Pre handler',
        description=('Function called before applying all steps. '
                     'It gets passed the setup tool as context.'),
        required=False)

    post_handler = GlobalObject(
        title='Post handler',
        description=('Function called after applying all steps. '
                     'It gets passed the setup tool as context.'),
        required=False)


def registerProfile(_context, name='default', title=None, description=None,
                    directory=None, provides=BASE, for_=None,
                    pre_handler=None, post_handler=None):
    """ Add a new profile to the registry.
    """
    product = _context.package.__name__
    if directory is None:
        directory = 'profiles/%s' % name

    if title is None:
        title = f"Profile '{name}' from '{product}'"

    if description is None:
        description = ''

    _context.action(
        discriminator=('registerProfile', product, name),
        callable=_profile_registry.registerProfile,
        args=(name, title, description, directory, product, provides, for_,
              pre_handler, post_handler),
    )


# genericsetup:exportStep

class IExportStepDirective(Interface):
    name = zope.schema.TextLine(
        title='Name',
        description='',
        required=True)

    title = MessageID(
        title='Title',
        description='',
        required=True)

    description = MessageID(
        title='Description',
        description='',
        required=True)

    handler = GlobalObject(
        title='Handler',
        description='',
        required=True)


def exportStep(context, name, handler, title=None, description=None):

    context.action(
        discriminator=('exportStep', name),
        callable=_export_step_registry.registerStep,
        args=(name, handler, title, description),
    )


# genericsetup:importStep

class IImportStepDirective(Interface):

    """Register import steps with the global registry.
    """

    name = zope.schema.TextLine(
        title='Name',
        description='',
        required=True)

    title = MessageID(
        title='Title',
        description='',
        required=True)

    description = MessageID(
        title='Description',
        description='',
        required=True)

    handler = GlobalObject(
        title='Handler',
        description='',
        required=True)


class IImportStepDependsDirective(Interface):

    name = zope.schema.TextLine(
        title='Name',
        description='Name of another import step that has to be run first',
        required=True)


class importStep:

    def __init__(self, context, name, title, description, handler):
        """ Add a new import step to the registry.
        """
        self.context = context
        self.discriminator = ('importStep', name)
        self.name = name
        self.handler = handler
        self.title = title
        self.description = description
        self.dependencies = ()

    def depends(self, context, name):
        self.dependencies += (name,)

    def __call__(self):

        self.context.action(
            discriminator=self.discriminator,
            callable=_import_step_registry.registerStep,
            args=(self.name, None, self.handler, self.dependencies, self.title,
                  self.description),
        )


# genericsetup:upgradeStep

class IUpgradeStepsDirective(Interface):

    """
    Define multiple upgrade steps without repeating all of the parameters
    """

    source = zope.schema.ASCII(
        title="Source version",
        required=False)

    destination = zope.schema.ASCII(
        title="Destination version",
        required=False)

    sortkey = zope.schema.Int(
        title="Sort key",
        required=False)

    profile = zope.schema.TextLine(
        title="GenericSetup profile id",
        required=True)


class IUpgradeStepsStepSubDirective(Interface):

    """
    Subdirective to IUpgradeStepsDirective
    """

    title = zope.schema.TextLine(
        title="Title",
        required=True)

    description = zope.schema.TextLine(
        title="Upgrade step description",
        required=False)

    handler = GlobalObject(
        title="Upgrade handler",
        required=True)

    checker = GlobalObject(
        title="Upgrade checker",
        required=False)


class IUpgradeStepDirective(IUpgradeStepsDirective,
                            IUpgradeStepsStepSubDirective):

    """
    Define a standalone upgrade step
    """


class IUpgradeDependsSubDirective(Interface):

    """
    Define a profile import step dependency of an upgrade process
    (i.e. a profile step that should be reimported when performing an
    upgrade due to a profile change.
    """

    title = zope.schema.TextLine(
        title="Title",
        required=True,
    )

    description = zope.schema.TextLine(
        title="Upgrade dependency description",
        required=False,
    )

    import_profile = zope.schema.TextLine(
        title="GenericSetup profile id to load, if not the same as the "
              "current profile.", required=False)

    import_steps = Tokens(
        title="Import steps to rerun",
        required=False,
        value_type=zope.schema.TextLine(title="Import step"),
    )

    run_deps = zope.schema.Bool(
        title="Run import step dependencies?",
        required=False,
    )

    purge = zope.schema.Bool(
        title="Import steps w/ purge=True?",
        required=False,
    )


class IUpgradeDependsDirective(IUpgradeStepsDirective,
                               IUpgradeDependsSubDirective):

    """
    Define a standalone upgrade profile import step dependency
    """


def upgradeStep(_context, title, profile, handler, description=None,
                source='*', destination='*', sortkey=0, checker=None):
    step = UpgradeStep(title, profile, source, destination, description,
                       handler, checker, sortkey)
    _context.action(
        discriminator=(
            'upgradeStep', profile, source, destination, handler, sortkey),
        callable=_registerUpgradeStep,
        args=(step,),
    )


def upgradeDepends(_context, title, profile, description=None,
                   import_profile=None, import_steps=[], source='*',
                   destination='*', run_deps=False, purge=False, checker=None,
                   sortkey=0):
    step = UpgradeDepends(title, profile, source, destination, description,
                          import_profile, import_steps, run_deps, purge,
                          checker, sortkey)
    _context.action(
        discriminator=('upgradeDepends', profile, source, destination,
                       import_profile, str(import_steps), checker, sortkey),
        callable=_registerUpgradeStep,
        args=(step,),
    )


class upgradeSteps:

    """
    Allows nested upgrade steps.
    """

    def __init__(self, _context, profile, source='*', destination='*',
                 sortkey=0):
        self.profile = profile
        self.source = source
        self.dest = destination
        self.sortkey = sortkey
        self.id = None

    def upgradeStep(self, _context, title, handler,
                    description=None, checker=None):
        """ nested upgradeStep directive """
        step = UpgradeStep(title, self.profile, self.source, self.dest,
                           description, handler, checker, self.sortkey)
        if self.id is None:
            self.id = _getHash(title, self.source, self.dest, self.sortkey)
        _context.action(
            discriminator=(
                'upgradeStep', self.profile, self.source, self.dest, handler,
                self.sortkey),
            callable=_registerNestedUpgradeStep,
            args=(step, self.id),
        )

    def upgradeDepends(self, _context, title, description=None,
                       import_profile=None, import_steps=[], run_deps=False,
                       purge=False, checker=None):
        """ nested upgradeDepends directive """
        step = UpgradeDepends(title, self.profile, self.source, self.dest,
                              description, import_profile, import_steps,
                              run_deps, purge, checker, self.sortkey)
        if self.id is None:
            self.id = _getHash(title, self.source, self.dest, self.sortkey)
        _context.action(
            discriminator=(
                'upgradeDepends', self.profile, self.source, self.dest,
                import_profile, str(import_steps), checker, self.sortkey),
            callable=_registerNestedUpgradeStep,
            args=(step, self.id),
        )

    def __call__(self):
        return ()
