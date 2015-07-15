``Products.GenericSetup``
=========================

Overview
--------

This product provides a mini-framework for expressing the configured
state of a Zope Site as a set of filesystem artifacts.  These artifacts
consist of declarative XML files, which spell out the configuration
settings for each "tool" in the site , and supporting scripts / templates,
in their "canonical" filesystem representations.


Configurations Included
-----------------------

The ``setup_tool`` knows how to export / import configurations and scripts
for the following components of a site:

- itself :)

- removal / creation of specified tools

- the role / permission map on the "site" object (its parent)

- properties of the site object

- "Placeful" utilities and adapters registered in the local
  site manager. Placeless utilities can only be imported.


Extending The Tool
------------------

Third-party products extend the tool by registering handlers for
import / export of their unique tools.

.. seealso::

    See :ref:`writing-handlers` for a step by step how-to.

Providing Profiles
------------------

GenericSetup doesn't ship with any profile. They have to be provided by
third-party products and depend on the registered handlers.

.. seealso::

    See :ref:`about-profiles` for more details.

Other Documentation
-------------------

.. toctree::
   :maxdepth: 2

   install
   handlers
   profiles
   CHANGES
   CREDITS
   glossary

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

