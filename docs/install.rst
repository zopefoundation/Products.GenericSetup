Installing :mod:`Products.GenericSetup`
=======================================

Installation via :command:`easy_install`
----------------------------------------

GenericSetup can be installed using the :mod:`setuptools` utility,
:command:`easy_install`, into the ``site-packages`` directory of your
Python installation::

  $ bin/easy_install Products.GenericSetup

Installation via :mod:`zc.buildout`
-----------------------------------

TBD

Manual Installation
-------------------

To install this package manually, without using :mod:`setuptools`,
simply untar the package file downloaded from the PyPI site and look for
the folder named ``GenericSetup`` underneath the ``Products`` folder at the
root of the extracted tarball. Copy or link this ``GenericSetup`` 
folder into the ``Products`` folder of your Zope2 instance and restart Zope.
