Glossary
========

.. glossary::

    site
        The instance in the Zope URL space which defines a "zone of service"
        for a set of tools.

    dotted name
        The Pythonic representation of the "path" to a given function /
        module, e.g. ``Products.GenericSetup.tool.exportToolset``.

    profile
        A "preset" configuration of a site, defined on the filesystem
        or in a tarball.

    base profile
        Profiles which represent the entire configuration of a given
        site, and have no dependencies.

    extension profile
        Profile fragments are used to modify a site created from a given
        :term:`base profile`.  They can be shipped with add-on products or
        used for customization steps.  Importing an :term:`extension
        profile` adds or overwrites existing settings in a fine-grained
        way.  An :term:`extension profile` cannot be exported.

    snapshot
        A profile which captures the state of the site's configuration
        at a point in time (e.g., immediately after creation of the site,
        or after importing an :term:`extension profile`.
