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
"""Local component registry export / import handler.

$Id$
"""

from operator import itemgetter

from zope.component import adapts
from zope.component import getUtilitiesFor
from zope.component import getSiteManager
from zope.component import queryMultiAdapter
from zope.component.interfaces import IComponentRegistry

from Acquisition import aq_base
from Acquisition import aq_parent

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import IComponentsHandlerBlacklist
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import _getDottedName
from Products.GenericSetup.utils import _resolveDottedName

BLACKLIST_SELF = _getDottedName(IComponentsHandlerBlacklist)


class ComponentRegistryXMLAdapter(XMLAdapterBase):

    """XML im- and exporter for a local component registry.
    """

    adapts(IComponentRegistry, ISetupEnviron)

    _LOGGER_ID = 'componentregistry'

    name = 'componentregistry'

    def _constructBlacklist(self):
        blacklist = set((BLACKLIST_SELF, ))
        utils = getUtilitiesFor(IComponentsHandlerBlacklist)
        for _, util in utils:
            names = [_getDottedName(i) for i in util.getExcludedInterfaces()]
            blacklist.update(names)
        return blacklist

    def _exportNode(self):
        node = self._doc.createElement('componentregistry')
        fragment = self._doc.createDocumentFragment()

        child = self._doc.createElement('adapters')
        child.appendChild(self._extractAdapters())
        self._logger.info('Adapters exported.')
        fragment.appendChild(child)

        child = self._doc.createElement('utilities')
        child.appendChild(self._extractUtilities())
        self._logger.info('Utilities exported.')
        fragment.appendChild(child)

        node.appendChild(fragment)

        return node

    def _importNode(self, node):
        if self.environ.shouldPurge():
            self._purgeAdapters()
            self._logger.info('Adapters purged.')
            self._purgeUtilities()
            self._logger.info('Utilities purged.')

        for child in node.childNodes:
            if child.nodeName == 'adapters':
                self._initAdapters(child)
                self._logger.info('Adapters registered.')
            if child.nodeName == 'utilities':
                self._initUtilities(child)
                self._logger.info('Utilities registered.')

    def _purgeAdapters(self):
        registrations = tuple(self.context.registeredAdapters())
        blacklist = self._constructBlacklist()

        for registration in registrations:
            factory = registration.factory
            required = registration.required
            provided = registration.provided
            name = registration.name
            if _getDottedName(provided) in blacklist:
                continue

            self.context.unregisterAdapter(factory=factory,
                                           required=required,
                                           provided=provided,
                                           name=name)

    def _purgeUtilities(self):
        registrations = tuple(self.context.registeredUtilities())
        blacklist = self._constructBlacklist()

        for registration in registrations:
            provided = registration.provided
            name = registration.name
            if _getDottedName(provided) in blacklist:
                continue
            self.context.unregisterUtility(provided=provided, name=name)

    def _initAdapters(self, node):
        blacklist = self._constructBlacklist()

        for child in node.childNodes:
            if child.nodeName != 'adapter':
                continue

            factory = _resolveDottedName(child.getAttribute('factory'))

            provided = child.getAttribute('provides')
            if provided in blacklist:
                continue

            provided = _resolveDottedName(provided)
            name = unicode(str(child.getAttribute('name')))

            for_ = child.getAttribute('for_')
            required = []
            for interface in for_.split(u' '):
                if interface:
                    required.append(_resolveDottedName(interface))

            self.context.registerAdapter(factory,
                                         required=required,
                                         provided=provided,
                                         name=name)

    def _getSite(self):
        # Get the site by either __parent__ or Acquisition
        site = getattr(self.context, '__parent__', None)
        if site is None:
            site = aq_parent(self.context)
        return site

    def _initUtilities(self, node):
        site = self._getSite()
        blacklist = self._constructBlacklist()

        current_utilities = self.context.registeredUtilities()

        for child in node.childNodes:
            if child.nodeName != 'utility':
                continue

            provided = child.getAttribute('interface')
            if provided in blacklist:
                continue

            provided = _resolveDottedName(provided)
            name = unicode(str(child.getAttribute('name')))

            component = child.getAttribute('component')
            component = component and _resolveDottedName(component) or None

            factory = child.getAttribute('factory')
            factory = factory and _resolveDottedName(factory) or None

            if component and factory:
                raise ValueError, "Can not specify both a factory and a " \
                                  "component in a utility registration."


            obj_path = child.getAttribute('object')
            if not component and not factory and obj_path is not None:
                # Support for registering the site itself
                if obj_path in ('', '/'):
                    obj = site
                else:
                    # BBB: filter out path segments, we did claim to support
                    # nested paths once
                    id_ = [p for p in obj_path.split('/') if p][0]
                    obj = getattr(site, id_, None)

                if obj is not None:
                    self.context.registerUtility(aq_base(obj), provided, name)
                else:
                    # Log an error, object not found
                    self._logger.warning("The object %s was not found, while "
                                         "trying to register an utility. The "
                                         "provided object definition was %s. "
                                         "The site used was: %s"
                                         % (repr(obj), obj_path, repr(site)))
            elif component:
                self.context.registerUtility(component, provided, name)
            elif factory:
                current = [ utility for utility in current_utilities
                                    if utility.provided==provided and 
                                       utility.name==name ]
                assert len(current) <=1

                if current and getattr(current[0], "factory", None)==factory:
                    continue

                try:
                    self.context.registerUtility(None, provided, name, factory=factory)
                except TypeError:
                    # zope.component < 3.5.0
                    self.context.registerUtility(factory(), provided, name)
            else:
                self._logger.warning("Invalid utility registration for "
                                     "interface %s" % provided)

    def _extractAdapters(self):
        fragment = self._doc.createDocumentFragment()

        registrations = [ {'factory': _getDottedName(reg.factory),
                           'provided': _getDottedName(reg.provided),
                           'required': reg.required,
                           'name': reg.name}
                          for reg in self.context.registeredAdapters() ]
        registrations.sort(key=itemgetter('name'))
        registrations.sort(key=itemgetter('provided'))
        blacklist = self._constructBlacklist()

        for reg_info in registrations:
            if reg_info['provided'] in blacklist:
                continue

            child = self._doc.createElement('adapter')

            for_ = u''
            for interface in reg_info['required']:
                for_ = for_ + _getDottedName(interface) + u'\n           '

            child.setAttribute('factory', reg_info['factory'])
            child.setAttribute('provides', reg_info['provided'])
            child.setAttribute('for_', for_.strip())
            if reg_info['name']:
                child.setAttribute('name', reg_info['name'])

            fragment.appendChild(child)

        return fragment

    def _extractUtilities(self):
        fragment = self._doc.createDocumentFragment()

        registrations = [ {'component': reg.component,
                           'factory' : getattr(reg, 'factory', None),
                           'provided': _getDottedName(reg.provided),
                           'name': reg.name}
                           for reg in self.context.registeredUtilities() ]
        registrations.sort(key=itemgetter('name'))
        registrations.sort(key=itemgetter('provided'))
        site = aq_base(self._getSite())
        blacklist = self._constructBlacklist()

        for reg_info in registrations:
            if reg_info['provided'] in blacklist:
                continue

            child = self._doc.createElement('utility')
            child.setAttribute('interface', reg_info['provided'])

            if reg_info['name']:
                child.setAttribute('name', reg_info['name'])

            if reg_info['factory'] is not None:
                child.setAttribute('factory', _getDottedName(reg_info['factory']))
            else:
                comp = reg_info['component']
                # check if the component is acquisition wrapped. If it is, export
                # an object reference instead of a factory reference
                if getattr(comp, 'aq_base', None) is not None:
                    if aq_base(comp) is site:
                        child.setAttribute('object', '')
                    elif hasattr(aq_base(comp), 'getId'):
                        child.setAttribute('object', comp.getId())
                    else:
                        # This is a five.localsitemanager wrapped utility
                        factory = _getDottedName(type(aq_base(comp)))
                        child.setAttribute('factory', factory)
                else:
                    factory = _getDottedName(type(comp))
                    child.setAttribute('factory', factory)

            fragment.appendChild(child)

        return fragment


def importComponentRegistry(context):
    """Import local components.
    """
    sm = getSiteManager(context.getSite())
    if sm is None or not IComponentRegistry.providedBy(sm):
        logger = context.getLogger('componentregistry')
        logger.info("Can not register components, as no registry was found.")
        return

    importer = queryMultiAdapter((sm, context), IBody)
    if importer:
        body = context.readDataFile('componentregistry.xml')
        if body is not None:
            importer.body = body

def exportComponentRegistry(context):
    """Export local components.
    """
    sm = getSiteManager(context.getSite())
    if sm is None or not IComponentRegistry.providedBy(sm):
        logger = context.getLogger('componentregistry')
        logger.debug("Nothing to export.")
        return

    exporter = queryMultiAdapter((sm, context), IBody)
    if exporter:
        body = exporter.body
        if body is not None:
            context.writeDataFile('componentregistry.xml', body,
                                  exporter.mime_type)

