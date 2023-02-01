##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""PythonScript export / import support.
"""

from zope.component import adapts

from ..interfaces import ISetupEnviron
from ..utils import BodyAdapterBase
from .interfaces import IPythonScript


class PythonScriptBodyAdapter(BodyAdapterBase):

    """Body im- and exporter for PythonScript.
    """

    adapts(IPythonScript, ISetupEnviron)

    def _exportBody(self):
        """Export the object as a file body.
        """
        return self.context.read().encode('utf-8')

    def _importBody(self, body):
        """Import the object from the file body.
        """
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        body = body.replace('\r\n', '\n').replace('\r', '\n')
        self.context.write(body)

    body = property(_exportBody, _importBody)

    mime_type = 'text/plain'

    suffix = '.py'
