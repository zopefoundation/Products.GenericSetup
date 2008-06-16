=======================
 Products.GenericSetup
=======================

This product provides a mini-framework for expressing the configured
state of a Zope Site as a set of filesystem artifacts.  These artifacts
consist of declarative XML files, which spell out the configuration
settings for each "tool" in the site , and supporting scripts / templates,
in their "canonical" filesystem representations.

.. contents::

Manual Installation
===================

If you want to install this package manually, without using setuptools,
simply untar the package file downloaded from the PyPI site and look for
the folder named "GenericSetup" underneath the "Products" folder at the
root of the extracted tarball. Copy or link this "GenericSetup" 
folder into your Zope "Products" folder and restart Zope.

Configurations Included
=======================

The 'setup_tool' knows how to export / import configurations and scripts
for the following tools:

- removal / creation of specified tools

- itself :)

- the role / permission map on the "site" object (its parent)

- properties of the site object

- placeful utilities and adapters registered in the local
  site manager. Placeless utilities can only be imported.

Extending The Tool
==================

Third-party products extend the tool by registering handlers for
import / export of their unique tools.

See doc/handlers.txt for a step by step how-to.

Providing Profiles
==================

GenericSetup doesn't ship with any profile. They have to be provided by
third-party products and depend on the registered handlers.

See doc/profiles.txt for more details.

Glossary
========

Site --
  The instance in the Zope URL space which defines a "zone of service"
  for a set of tools.

Profile --
  A "preset" configuration of a site, defined on the filesystem

Snapshot --
  "Frozen" site configuration, captured within the setup tool

"dotted name" --
  The Pythonic representation of the "path" to a given function /
  module, e.g. 'Products.GenericSetup.tool.exportToolset'.
