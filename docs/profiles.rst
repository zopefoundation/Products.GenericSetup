.. _about-profiles:

About Profiles
==============

Overview
--------

``GenericSetup`` uses two different kinds of profiles:  a :term:`base
profile` captures the entire state of the site, while an :term:`extension
profile` represents an add-on / delta to be applied to the site's
configuration.


Registering Profiles
--------------------

By convention profiles are stored in a ``profiles`` directory within a
Zope2 product. They have to be registered explicitly using either the
:meth:`Products.GenericSetup.profile_registry.registerProfile` API or the
equivalent ``genericsetup:registerProfile`` ZCML directive.

Here is example ZCML for a Zope2 product, ``MyProduct``, which extends
another product, ``BaseProduct``::

  <genericsetup:registerProfile
      name="install"
      title="Install MyProduct Extension"
      description="Adds local settings necessary for MyProduct."
      provides="Products.GenericSetup.interfaces.EXTENSION"
      for="Products.BaseProduct.interfaces.IBaseRoot"
      />

.. seealso::

   :class:`Products.GenericSetup.zcml.IRegisterProfileDirective` defines
   the API for this directive.

Alternatively, profiles can be registered by calling the
:func:`Products.GenericSetup.profile_registry.registerProfile` API.

Here is the code for the same example::

    from Products.BaseProduct.interfaces import IBaseRoot
    from Products.GenericSetup import EXTENSION
    from Products.GenericSetup import profile_registry

    profile_registry.registerProfile(
            name='install',
            title='Install MyProduct Extension',
            description='Adds local settings necessary for MyProduct.',
            path='profiles/install',
            product='Products.MyProduct',
            profile_type=EXTENSION,
            for_=IBaseRoot)

.. seealso::

    See IProfileRegistry.registerProfile for further details.

.. note::
    Using this API for product initialization is deprecated.

Update Directives
-----------------

For some XML elements there are additional attributes and values to
specify update directives. They are only useful for extension profiles and
you will never see them in snapshots and exports.

The following directives are generally useful for container elements and
implemented by some setup handlers. Products using GenericSetup can also
implement other update directives.

``id="*"`` wildcard

    Updates all existing items in the container with the same settings.

``remove``

    Removes the specified item if it exists.

``insert-before`` and ``insert-after``

    ``insert-before`` and ``insert-after`` specify the position of a new
    item relative to an existing item. If they are omitted or not valid,
    items are appended. You can also use ``*`` as wildcard. This will
    insert the new item at the top (before all existing items) or the
    bottom (after all existing items). If an item with the given ID exists
    already, it is moved to the specified position. This directive makes
    only sense for ordered containers.

Other Special Directives
------------------------

``purge``

    By default existing settings are purged before applying settings from
    base profiles. Extension profiles are applied in update mode. This
    directive overrides the default behavior. If True the existing settings
    of the current object are always purged, if False they are not purged.
