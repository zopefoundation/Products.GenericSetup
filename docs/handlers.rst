.. _writing-handlers:

How-to: Writing setup handlers for ``Products.GenericSetup``
============================================================

If your product subclasses existing tools or provides new tools (or new
sub-object classes), it might need to supply its own setup handlers in
order to support exporting / importing tool settings using GenericSetup.

Step 1:
-------

Identify those classes in your product that need their own setup handlers.
In theory you don't need your own handlers for classes which implement a
CMF tool interface that already has a setup adapter.  In practice the
adapters shipped with the CMF sometimes use methods that are not part of
the interface, so you have to verify that they really work for your classes.

Step 2:
-------

Make sure those classes that need setup handlers have Zope3 style
interfaces.  Later you will write setup adapters for those interfaces.

Step 3:
-------

Create an ``exportimport`` module inside your product. If you plan to write
many setup handlers this can be a sub-package.

Step 4:
-------

Decide which kind of setup handler you need:

body adapter
   For objects represented by a complete file body. Provides
   ``Products.GenericSetup.interfaces.IBody``.

XML adapter
   A 'body adapter' in XML format. Also provides
   ``Products.GenericSetup.interfaces.IBody``, but has its own
   base class because XML is the preferred format.

node adapter
   For sub-objects represented by an XML node of the parent's XML document.
   Provides ``Products.GenericSetup.interfaces.INode``. This is useful for
   sub-objects of complex tools. Custom catalog index or action classes
   need this kind of adapter.

import and export steps
   Top level handlers can be registered to manage import steps and / or export
   steps and call the body adapters. 

If you use the base classes from :mod:`Products.GenericSetup.utils`, XML and
node adapters are implemented in a very similar way. Both can mix in
``ObjectManagerHelpers`` and ``PropertyManagerHelpers``.

Step 5:
-------

:mod:`Products.CMFCore.exportimport` contains many examples for XML and
node adapters. If you need a pure body adapter,
:mod:`Products.GenericSetup.PythonScripts` would be a good
example. Follow those examples and write your own multi adapter, register
it for the interface of your class and for
``Products.GenericSetup.interfaces.ISetupEnviron`` and don't forget
to write unit tests.

Adapters follow the convention that ``self.context`` is always the primary
adapted object, so the minimal setup context (``ISetupEnviron``) used in these
multi adapters is ``self.environ``.

XML and body adapters are always also small node adapters. This way the
XML file of the container contains the information that is necessary to
create an empty object. The handler of the container has to set up
sub-objects before we can adapt them and configure them with their own
handlers. The base classes in :mod:`Products.GenericSetup.utils`
will care about that.

Step 6:
-------

If your adapter is a top-level adapter (e.g for a tool), you need import
and export steps that know how to use the adapter. Again there are many
examples in :mod:`Products.CMFCore.exportimport`.

To make those steps available you have to add them to ``export_steps.xml``
and ``import_steps.xml`` of a setup profile and to load that profile into the
setup tool.

Step 7:
-------

Now you are done. To ship default settings with your product, make your
settings through the ZMI (or set your stuff up the old way if you have old
setup code like an ``Install.py``) and export your settings using the setup
tool.  Unpack the exported tarball into a ``profiles`` subdirectory of your
product, and then add ``gs:registerProfile`` entries to its ``configure.zcml``
file to register that directory as a :term:`base profile` or
:term:`extension profile`.

.. seealso::

    See :ref:`about-profiles` for more details.
