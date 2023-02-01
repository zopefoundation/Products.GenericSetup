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
""" GenericSetup product utilities
"""

import hashlib
import os
from html import escape
from inspect import getdoc
from logging import getLogger
from xml.dom.minidom import Document
from xml.dom.minidom import Element
from xml.dom.minidom import Node
from xml.dom.minidom import _nssplit
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.Common import package_home
from OFS.interfaces import IOrderedContainer
from Products.Five.utilities.interfaces import IMarkerInterfaces
from zope.component import queryMultiAdapter
from zope.configuration.name import resolve
from zope.interface import directlyProvides
from zope.interface import implementer
from zope.interface import implementer_only
from ZPublisher.Converters import type_converters
from ZPublisher.HTTPRequest import default_encoding

from .exceptions import BadRequest
from .interfaces import IBody
from .interfaces import INode
from .interfaces import ISetupTool
from .permissions import ManagePortal


_pkgdir = package_home(globals())
_wwwdir = os.path.join(_pkgdir, 'www')
_xmldir = os.path.join(_pkgdir, 'xml_templates')

# Please note that these values may change. Always import
# the values from here instead of using the values directly.
CONVERTER, DEFAULT, KEY = 1, 2, 3
I18NURI = 'http://xml.zope.org/namespaces/i18n'

# If we have type converters for lines and string, which should be always,
# then we may need to call these converters on Zope 5.3 and higher.
# This is because since Zope 5.3, the lines converter gives
# text instead of bytes.
# See https://github.com/zopefoundation/Products.GenericSetup/issues/109
if (
    "lines" in type_converters
    and "string" in type_converters
    and isinstance(type_converters["lines"]("blah")[0], str)
):
    LINES_HAS_TEXT = True
else:
    # Older Zope
    LINES_HAS_TEXT = False


def _getDottedName(named):

    if isinstance(named, str):
        return str(named)

    try:
        dotted = f'{named.__module__}.{named.__name__}'
    except AttributeError:
        raise ValueError('Cannot compute dotted name: %s' % named)

    # remove leading underscore names if possible

    # Step 1: check if there is a short version
    short_dotted = '.'.join([n for n in dotted.split('.')
                             if not n.startswith('_')])
    if short_dotted == dotted:
        return dotted

    # Step 2: check if short version can be resolved
    try:
        short_resolved = _resolveDottedName(short_dotted)
    except (ValueError, ImportError):
        return dotted

    # Step 3: check if long version resolves to the same object
    try:
        resolved = _resolveDottedName(dotted)
    except (ValueError, ImportError):
        raise ValueError('Cannot compute dotted name: %s' % named)
    if short_resolved is not resolved:
        return dotted

    return short_dotted


def _resolveDottedName(dotted):
    __traceback_info__ = dotted

    try:
        return resolve(dotted)
    except ModuleNotFoundError:
        return


def _extractDocstring(func, default_title, default_description):
    try:
        doc = getdoc(func)
        lines = doc.split('\n')

    except AttributeError:

        title = default_title
        description = default_description

    else:
        title = lines[0]

        if len(lines) > 1 and lines[1].strip() == '':
            del lines[1]

        description = '\n'.join(lines[1:])

    return title, description


def _version_for_print(version):
    """Return a version suitable for printing/logging.

    Versions of profiles and destinations of upgrade steps
    are likely tuples.  We join them with dots.

    Used internally when logging.
    """
    if isinstance(version, str):
        return version
    if isinstance(version, tuple):
        return ".".join(version)
    return str(version)


##############################################################################
# WARNING: PLEASE DON'T USE THE CONFIGURATOR PATTERN. THE RELATED BASE CLASSES
# WILL BECOME DEPRECATED AS SOON AS GENERICSETUP ITSELF NO LONGER USES THEM.

class ImportConfiguratorBase(Implicit):
    # old code, will become deprecated
    """ Synthesize data from XML description.
    """
    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, site, encoding='utf-8'):

        self._site = site
        self._encoding = None

    @security.protected(ManagePortal)
    def parseXML(self, xml):
        """ Pseudo API.
        """
        reader = getattr(xml, 'read', None)

        if reader is not None:
            xml = reader()

        if isinstance(xml, bytes):
            xml = xml.decode('utf-8')

        dom = parseString(xml)
        root = dom.documentElement

        return self._extractNode(root)

    def _extractNode(self, node):
        """ Please see docs/configurator.txt for information about the
        import mapping syntax.
        """
        nodes_map = self._getImportMapping()
        if node.nodeName not in nodes_map:
            nodes_map = self._getSharedImportMapping()
            if node.nodeName not in nodes_map:
                raise ValueError('Unknown node: %s' % node.nodeName)
        node_map = nodes_map[node.nodeName]
        info = {}

        for name, val in node.attributes.items():
            key = node_map[name].get(KEY, str(name))
            val = self._encoding and val.encode(self._encoding) or val
            info[key] = val

        for child in node.childNodes:
            name = child.nodeName

            if name == '#comment':
                continue

            if not name == '#text':
                key = node_map[name].get(KEY, str(name))
                info[key] = info.setdefault(key, ()) + (
                                                    self._extractNode(child),)

            elif '#text' in node_map:
                key = node_map['#text'].get(KEY, 'value')
                val = child.nodeValue.lstrip()
                val = self._encoding and val.encode(self._encoding) or val
                info[key] = info.setdefault(key, '') + val

        for k, v in node_map.items():
            key = v.get(KEY, k)

            if DEFAULT in v and key not in info:
                if isinstance(v[DEFAULT], str):
                    info[key] = v[DEFAULT] % info
                else:
                    info[key] = v[DEFAULT]

            elif CONVERTER in v and key in info:
                info[key] = v[CONVERTER](info[key])

            if key is None:
                info = info[key]

        return info

    def _getSharedImportMapping(self):

        return {
          'object': {'i18n:domain': {},
                     'name': {KEY: 'id'},
                     'meta_type': {},
                     'insert-before': {},
                     'insert-after': {},
                     'property': {KEY: 'properties', DEFAULT: ()},
                     'object': {KEY: 'objects', DEFAULT: ()},
                     'xmlns:i18n': {}},
          'property': {'name': {KEY: 'id'},
                       '#text': {KEY: 'value', DEFAULT: ''},
                       'element': {KEY: 'elements', DEFAULT: ()},
                       'type': {},
                       'select_variable': {},
                       'i18n:translate': {}},
          'element': {'value': {KEY: None}},
          'description': {'#text': {KEY: None, DEFAULT: ''}}}

    def _convertToBoolean(self, val):

        return val.lower() in ('true', 'yes', '1')

    def _convertToUnique(self, val):

        assert len(val) == 1
        return val[0]


InitializeClass(ImportConfiguratorBase)


class ExportConfiguratorBase(Implicit):
    # old code, will become deprecated
    """ Synthesize XML description.
    """
    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, site, encoding='utf-8'):

        self._site = site
        self._encoding = encoding
        self._template = self._getExportTemplate()

    @security.protected(ManagePortal)
    def generateXML(self, **kw):
        """ Pseudo API.
        """
        return self._template(**kw)


InitializeClass(ExportConfiguratorBase)

#
##############################################################################


class _LineWrapper:

    def __init__(self, writer, indent, addindent, newl, max):
        self._writer = writer
        self._indent = indent
        self._addindent = addindent
        self._newl = newl
        self._max = max
        self._length = 0
        self._queue = self._indent

    def queue(self, text):
        self._queue += text

    def write(self, text='', enforce=False):
        self._queue += text

        if 0 < self._length > self._max - len(self._queue):
            self._writer.write(self._newl)
            self._length = 0
            self._queue = f'{self._indent}{self._addindent} {self._queue}'

        if self._queue != self._indent:
            self._writer.write(self._queue)
            self._length += len(self._queue)
            self._queue = ''

        if 0 < self._length and enforce:
            self._writer.write(self._newl)
            self._length = 0
            self._queue = self._indent


class _Element(Element):

    """minidom element with 'pretty' XML output.
    """

    def writexml(self, writer, indent="", addindent="", newl=""):
        # indent = current indentation
        # addindent = indentation to add to higher levels
        # newl = newline string
        wrapper = _LineWrapper(writer, indent, addindent, newl, 78)
        wrapper.write('<%s' % self.tagName)

        # move 'name', 'meta_type' and 'title' to the top, sort the rest
        attrs = self._get_attributes()
        a_names = sorted(attrs.keys())
        if 'title' in a_names:
            a_names.remove('title')
            a_names.insert(0, 'title')
        if 'meta_type' in a_names:
            a_names.remove('meta_type')
            a_names.insert(0, 'meta_type')
        if 'name' in a_names:
            a_names.remove('name')
            a_names.insert(0, 'name')

        for a_name in a_names:
            wrapper.write()
            a_value = attrs[a_name].value
            if a_value is None:
                a_value = ""
            else:
                a_value = escape(a_value, quote=True)

            wrapper.queue(f' {a_name}="{a_value}"')

        if self.childNodes:
            wrapper.queue('>')
            for node in self.childNodes:
                if node.nodeType == Node.TEXT_NODE:
                    data = escape(node.data)
                    textlines = data.splitlines()
                    if textlines:
                        wrapper.queue(textlines.pop(0))
                    if textlines:
                        for textline in textlines:
                            wrapper.write('', True)
                            wrapper.queue(f'{addindent}{textline}')
                else:
                    wrapper.write('', True)
                    node.writexml(writer, indent + addindent, addindent, newl)
            wrapper.write('</%s>' % self.tagName, True)
        else:
            wrapper.write('/>', True)


class PrettyDocument(Document):

    """minidom document with 'pretty' XML output.
    """

    def createElement(self, tagName):
        e = _Element(tagName)
        e.ownerDocument = self
        return e

    def createElementNS(self, namespaceURI, qualifiedName):
        prefix, _localName = _nssplit(qualifiedName)
        e = _Element(qualifiedName, namespaceURI, prefix)
        e.ownerDocument = self
        return e

    def writexml(self, writer, indent="", addindent="", newl="",
                 encoding='utf-8', standalone=None):
        # `standalone` was added in Python 3.9 but is ignored here
        if encoding is None:
            writer.write('<?xml version="1.0"?>\n')
        else:
            writer.write('<?xml version="1.0" encoding="%s"?>\n' % encoding)
        for node in self.childNodes:
            node.writexml(writer, indent, addindent, newl)

    def toprettyxml(self, indent='\t', newl='\n', encoding='utf-8'):
        return super().toprettyxml(indent, newl, encoding)


@implementer(INode)
class NodeAdapterBase:

    """Node im- and exporter base.
    """

    _encoding = 'utf-8'
    _LOGGER_ID = ''

    def __init__(self, context, environ):
        self.context = context
        self.environ = environ
        self._logger = environ.getLogger(self._LOGGER_ID)
        self._doc = PrettyDocument()

    def _getObjectNode(self, name, i18n=True):
        node = self._doc.createElement(name)
        node.setAttribute('name', self.context.getId())
        node.setAttribute('meta_type', self.context.meta_type)
        i18n_domain = getattr(self.context, 'i18n_domain', None)
        if i18n and i18n_domain:
            node.setAttributeNS(I18NURI, 'i18n:domain', i18n_domain)
            self._i18n_props = ('title', 'description')
        return node

    def _getNodeText(self, node):
        text = ''
        for child in node.childNodes:
            if child.nodeName != '#text':
                continue
            lines = [line.lstrip() for line in child.nodeValue.splitlines()]
            text += '\n'.join(lines)
        return text

    def _convertToBoolean(self, val):
        return val.lower() in ('true', 'yes', '1')


@implementer_only(IBody)
class BodyAdapterBase(NodeAdapterBase):

    """Body im- and exporter base.
    """

    def _exportSimpleNode(self):
        """Export the object as a DOM node.
        """
        if ISetupTool.providedBy(self.context):
            return None
        return self._getObjectNode('object', False)

    def _importSimpleNode(self, node):
        """Import the object from the DOM node.
        """

    node = property(_exportSimpleNode, _importSimpleNode)

    def _exportBody(self):
        """Export the object as a file body.
        """
        return b''

    def _importBody(self, body):
        """Import the object from the file body.
        """

    body = property(_exportBody, _importBody)

    mime_type = 'text/plain'

    name = ''

    suffix = ''


@implementer_only(IBody)
class XMLAdapterBase(BodyAdapterBase):

    """XML im- and exporter base.
    """

    def _exportBody(self):
        """Export the object as a file body.
        """
        self._doc.appendChild(self._exportNode())
        xml = self._doc.toprettyxml(' ', encoding=self._encoding)
        self._doc.unlink()
        return xml

    def _importBody(self, body):
        """Import the object from the file body.
        """
        try:
            dom = parseString(body)
        except ExpatError as e:
            filename = (self.filename or
                        '/'.join(self.context.getPhysicalPath()))
            raise ExpatError(f'{filename}: {e}')

        # Replace the encoding with the one from the XML
        self._encoding = dom.encoding or self._encoding
        self._importNode(dom.documentElement)

    body = property(_exportBody, _importBody)

    mime_type = 'text/xml'

    name = ''

    suffix = '.xml'

    filename = ''  # for error reporting during import


class ObjectManagerHelpers:

    """ObjectManager in- and export helpers.
    """

    def _extractObjects(self):
        fragment = self._doc.createDocumentFragment()
        objects = self.context.objectValues()
        if not IOrderedContainer.providedBy(self.context):
            objects = list(objects)
            objects.sort(key=lambda x: x.getId())
        for obj in objects:
            exporter = queryMultiAdapter((obj, self.environ), INode)
            if exporter:
                node = exporter.node
                if node is not None:
                    fragment.appendChild(exporter.node)
        return fragment

    def _purgeObjects(self):
        for obj_id, obj in self.context.objectItems():
            if ISetupTool.providedBy(obj):
                continue
            self.context._delObject(obj_id)

    def _initObjects(self, node):
        import Products
        for child in node.childNodes:
            if child.nodeName != 'object':
                continue
            if child.hasAttribute('deprecated'):
                continue
            parent = self.context

            obj_id = str(child.getAttribute('name'))
            if self._convertToBoolean(child.getAttribute('remove') or 'False'):
                if obj_id in parent.objectIds():
                    parent._delObject(obj_id)
                continue

            if obj_id not in parent.objectIds():
                meta_type = str(child.getAttribute('meta_type'))
                __traceback_info__ = obj_id, meta_type
                for mt_info in Products.meta_types:
                    if mt_info['name'] == meta_type:
                        parent._setObject(obj_id, mt_info['instance'](obj_id))
                        break
                else:
                    raise ValueError("unknown meta_type '%s'" % meta_type)

            if child.hasAttribute('insert-before'):
                insert_before = child.getAttribute('insert-before')
                if insert_before == '*':
                    parent.moveObjectsToTop(obj_id)
                else:
                    try:
                        position = parent.getObjectPosition(insert_before)
                        if parent.getObjectPosition(obj_id) < position:
                            position -= 1
                        parent.moveObjectToPosition(obj_id, position)
                    except ValueError:
                        pass
            elif child.hasAttribute('insert-after'):
                insert_after = child.getAttribute('insert-after')
                if insert_after == '*':
                    parent.moveObjectsToBottom(obj_id)
                else:
                    try:
                        position = parent.getObjectPosition(insert_after)
                        if parent.getObjectPosition(obj_id) < position:
                            position -= 1
                        parent.moveObjectToPosition(obj_id, position + 1)
                    except ValueError:
                        pass

            obj = getattr(self.context, obj_id)
            importer = queryMultiAdapter((obj, self.environ), INode)
            if importer:
                importer.node = child


class PropertyManagerHelpers:

    """PropertyManager im- and export helpers.

      o Derived classes can supply a '_PROPERTIES' scehma, which is then used
        to mock up a temporary propertysheet for the object.  The adapter's
        methods ('_extractProperties', '_purgeProperties', '_initProperties')
        then run against that propertysheet.
    """
    _PROPERTIES = ()

    _encoding = default_encoding

    def __init__(self, context, environ):
        from OFS.PropertyManager import PropertyManager
        if not isinstance(context, PropertyManager):
            context = self._fauxAdapt(context)

        super().__init__(context, environ)

    def _fauxAdapt(self, context):
        from OFS.PropertySheets import PropertySheet

        class Adapted(PropertySheet):
            def __init__(self, real, properties):
                self._real = real
                self._properties = properties

            def p_self(self):
                return self

            def v_self(self):
                return self._real

            def propdict(self):
                # PropertyManager method used by _initProperties
                return {p['id']: p for p in self._properties}

        return Adapted(context, self._PROPERTIES)

    def _extractProperties(self):
        fragment = self._doc.createDocumentFragment()

        for prop_map in self.context._propertyMap():
            prop_id = prop_map['id']
            if prop_id == 'i18n_domain':
                continue

            # Don't export read-only nodes
            if 'w' not in prop_map.get('mode', 'wd'):
                continue

            node = self._doc.createElement('property')
            node.setAttribute('name', prop_id)

            prop = self.context.getProperty(prop_id)
            if prop is None:
                continue
            if isinstance(prop, (tuple, list)):
                for value in prop:
                    if isinstance(value, bytes):
                        value = value.decode(self._encoding)
                    child = self._doc.createElement('element')
                    child.setAttribute('value', value)
                    node.appendChild(child)
            else:
                if prop_map.get('type') == 'boolean':
                    prop = str(bool(prop))
                elif prop_map.get('type') == 'date':
                    if prop.timezoneNaive():
                        prop = str(prop).rsplit(None, 1)[0]
                    else:
                        prop = str(prop)
                elif isinstance(prop, bytes):
                    prop = prop.decode(self._encoding)
                elif isinstance(prop, ((int,), float)):
                    prop = str(prop)
                elif not isinstance(prop, str):
                    prop = prop.decode(self._encoding)
                child = self._doc.createTextNode(prop)
                node.appendChild(child)

            if 'd' in prop_map.get('mode', 'wd') and not prop_id == 'title':
                prop_type = prop_map.get('type', 'string')
                node.setAttribute('type', prop_type)
                select_variable = prop_map.get('select_variable', None)
                if select_variable is not None:
                    node.setAttribute('select_variable', select_variable)

            if hasattr(self, '_i18n_props') and prop_id in self._i18n_props:
                node.setAttribute('i18n:translate', '')

            fragment.appendChild(node)

        return fragment

    def _purgeProperties(self):
        for prop_map in self.context._propertyMap():
            mode = prop_map.get('mode', 'wd')
            if 'w' not in mode:
                continue
            prop_id = prop_map['id']
            if 'd' in mode and not prop_id == 'title':
                self.context._delProperty(prop_id)
            else:
                prop_type = prop_map.get('type')
                if prop_type == 'multiple selection':
                    prop_value = ()
                elif prop_type in ('int', 'float'):
                    prop_value = 0
                elif prop_type == 'date':
                    prop_value = '1970/01/01 00:00:00 UTC'  # DateTime(0) UTC
                else:
                    prop_value = ''
                self.context._updateProperty(prop_id, prop_value)

    def _initProperties(self, node):
        obj = self.context
        if node.hasAttribute('i18n:domain'):
            i18n_domain = str(node.getAttribute('i18n:domain'))
            obj._updateProperty('i18n_domain', i18n_domain)
        for child in node.childNodes:
            if child.nodeName != 'property':
                continue
            remove = self._convertToBoolean(
                child.getAttribute('remove') or 'False')
            prop_id = str(child.getAttribute('name'))
            prop_map = obj.propdict().get(prop_id, None)

            if prop_map is None:
                if remove:
                    continue
                if child.hasAttribute('type'):
                    val = str(child.getAttribute('select_variable'))
                    prop_type = str(child.getAttribute('type'))
                    obj._setProperty(prop_id, val, prop_type)
                    prop_map = obj.propdict().get(prop_id, None)
                else:
                    raise ValueError("undefined property '%s'" % prop_id)

            if remove:
                if 'd' not in prop_map.get('mode', 'wd'):
                    raise BadRequest('%s cannot be deleted' % prop_id)
                obj._delProperty(prop_id)
                continue

            if 'w' not in prop_map.get('mode', 'wd'):
                raise BadRequest('%s cannot be changed' % prop_id)

            new_elements = []
            remove_elements = []
            for sub in child.childNodes:
                if sub.nodeName == 'element':
                    value = sub.getAttribute('value')
                    if prop_map.get('type') not in (
                            'ulines', 'multiple selection'):
                        value = value.encode(self._encoding)
                    if self._convertToBoolean(sub.getAttribute('remove')
                                              or 'False'):
                        remove_elements.append(value)
                        if value in new_elements:
                            new_elements.remove(value)
                    else:
                        new_elements.append(value)
                        if value in remove_elements:
                            remove_elements.remove(value)

            if LINES_HAS_TEXT and obj.getPropertyType(prop_id) == 'lines':
                # Since Zope 5.3, lines should contain text, not bytes.
                # https://github.com/zopefoundation/Products.GenericSetup/issues/109
                new_elements = _convert_lines(new_elements, self._encoding)
                remove_elements = _convert_lines(
                    remove_elements, self._encoding)

            if prop_map.get('type') in ('lines', 'tokens', 'ulines',
                                        'multiple selection'):
                prop_value = tuple(new_elements) or ()
            elif prop_map.get('type') == 'boolean':
                prop_value = self._convertToBoolean(self._getNodeText(child))
            else:
                # if we pass a *string* to _updateProperty, all other values
                # are converted to the right type
                prop_value = self._getNodeText(child)

            if not self._convertToBoolean(child.getAttribute('purge')
                                          or 'True'):
                # If the purge attribute is False, merge sequences
                prop = obj.getProperty(prop_id)
                # Before Zope 5.3, lines contained bytes.
                # After, they contain text.
                # We may need to convert the existing property value first,
                # otherwise we may be combining bytes and text.
                # See zopefoundation/Products.GenericSetup/issues/109
                if LINES_HAS_TEXT and obj.getPropertyType(prop_id) == 'lines':
                    prop = _convert_lines(prop, self._encoding)
                if isinstance(prop, (tuple, list)):
                    prop_value = (tuple([p for p in prop
                                         if p not in prop_value and
                                         p not in remove_elements]) +
                                  tuple(prop_value))

            if isinstance(prop_value, (bytes, str)):
                prop_type = obj.getPropertyType(prop_id) or 'string'
                if prop_type in type_converters:
                    prop_converter = type_converters[prop_type]
                    # The type_converters use the ZPublisher default_encoding
                    # for decoding bytes!
                    if self._encoding.lower() != default_encoding:
                        prop_value = _de_encode_value(
                            prop_value, self._encoding, prop_converter)
                    else:
                        prop_value = prop_converter(prop_value)
            obj._updateProperty(prop_id, prop_value)


def _de_encode_value(prop_value, encoding, converter):
    if isinstance(prop_value, bytes):
        u_prop_value = prop_value.decode(encoding)
        prop_value = u_prop_value.encode(default_encoding)
    prop_value = converter(prop_value)
    if isinstance(prop_value, bytes):
        u_prop_value = prop_value.decode(default_encoding)
        prop_value = u_prop_value.encode(encoding)
    return prop_value


def _convert_lines(values, encoding):
    # Only called when LINES_HAS_TEXT is True.
    if not isinstance(values, (list, tuple)):
        values = values.splitlines()
    if encoding.lower() == default_encoding:
        converter = type_converters['lines']
        return converter(values)
    # According to the tests, we support non utf-8 encodings like iso-8859-1.
    converter = type_converters['string']
    return [
        _de_encode_value(prop_value, encoding, converter)
        for prop_value in values
    ]


class MarkerInterfaceHelpers:

    """Marker interface im- and export helpers.
    """

    def _extractMarkers(self):
        fragment = self._doc.createDocumentFragment()
        adapted = IMarkerInterfaces(self.context)

        for marker_id in adapted.getDirectlyProvidedNames():
            node = self._doc.createElement('marker')
            node.setAttribute('name', marker_id)
            fragment.appendChild(node)

        return fragment

    def _purgeMarkers(self):
        directlyProvides(self.context)

    def _initMarkers(self, node):
        markers = []
        adapted = IMarkerInterfaces(self.context)

        for child in node.childNodes:
            if child.nodeName != 'marker':
                continue
            markers.append(str(child.getAttribute('name')))

        adapted.update(adapted.dottedToInterfaces(markers))


def exportObjects(obj, parent_path, context):
    """ Export subobjects recursively.
    """
    exporter = queryMultiAdapter((obj, context), IBody)
    path = '{}{}'.format(parent_path, obj.getId().replace(' ', '_'))
    if exporter:
        if exporter.name:
            path = f'{parent_path}{exporter.name}'
        filename = f'{path}{exporter.suffix}'
        body = exporter.body
        if body is not None:
            context.writeDataFile(filename, body, exporter.mime_type)

    if getattr(obj, 'objectValues', False):
        for sub in obj.objectValues():
            exportObjects(sub, path + '/', context)


def importObjects(obj, parent_path, context):
    """ Import subobjects recursively.
    """
    importer = queryMultiAdapter((obj, context), IBody)
    path = '{}{}'.format(parent_path, obj.getId().replace(' ', '_'))
    __traceback_info__ = path
    if importer:
        if importer.name:
            path = f'{parent_path}{importer.name}'
        filename = f'{path}{importer.suffix}'
        body = context.readDataFile(filename)
        if body is not None:
            importer.filename = filename  # for error reporting
            importer.body = body

    if getattr(obj, 'objectValues', False):
        for sub in obj.objectValues():
            importObjects(sub, path + '/', context)


def _computeTopologicalSort(steps):
    result = []
    graph = [(x['id'], x['dependencies']) for x in steps]

    unresolved = []

    while 1:
        for node, edges in graph:

            after = -1
            resolved = 0

            for edge in edges:

                if edge in result:
                    resolved += 1
                    after = max(after, result.index(edge))

            if len(edges) > resolved:
                unresolved.append((node, edges))
            else:
                result.insert(after + 1, node)

        if not unresolved:
            break
        if len(unresolved) == len(graph):
            # Nothing was resolved in this loop. There must be circular or
            # missing dependencies. Just add them to the end. We can't
            # raise an error, because checkComplete relies on this method.
            logger = getLogger('GenericSetup')
            log_msg = 'There are unresolved or circular dependencies. '\
                      'Graphviz diagram:: digraph dependencies {'
            for step in steps:
                step_id = step['id']
                for dependency in step['dependencies']:
                    log_msg += f'"{step_id}" -> "{dependency}"; '
                if not step['dependencies']:
                    log_msg += '"%s";' % step_id
            for unresolved_key, _ignore in unresolved:
                log_msg += '"%s" [color=red,style=filled]; ' % unresolved_key
            log_msg += '}'
            logger.warning(log_msg)

            for node, edges in unresolved:
                result.append(node)
            break
        graph = unresolved
        unresolved = []

    return result


def _getProductPath(product_name):
    """ Return the absolute path of the product's directory.
    """
    try:
        # BBB: for GenericSetup 1.1 style product names
        product = __import__(f'Products.{product_name}', globals(), {},
                             ['initialize'])
    except ImportError:
        try:
            product = __import__(product_name, globals(), {}, ['initialize'])
        except ImportError:
            raise ValueError(f'Not a valid product name: {product_name}')

    return product.__path__[0]


def _getHash(*args):
    """return a stable md hash of given string arguments"""
    base = "".join([str(x) for x in args])
    hashmd5 = hashlib.md5(base.encode('utf8'))
    return hashmd5.hexdigest()
