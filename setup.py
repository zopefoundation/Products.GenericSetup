import os
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))
package = os.path.join(here, 'Products', 'GenericSetup')

def _package_doc(name):
    f = open(os.path.join(package, name))
    return f.read()

NAME = 'GenericSetup'

VERSION = _package_doc('version.txt').strip()
if VERSION.startswith(NAME):
    VERSION = VERSION[len(NAME):]
while VERSION and VERSION[0] in '-_.':
    VERSION = VERSION[1:]

_boundary = '\n' + ('-' * 60) + '\n'
README = (open(os.path.join(here, 'README.txt')).read()
        + _boundary + _package_doc('README.txt')
        + _boundary + _package_doc('CHANGES.txt')
         )

setup(name='Products.GenericSetup',
      version=VERSION,
      description='Read Zope configuration state from profile dirs / tarballs',
      long_description=README,
      classifiers=[
        "Development Status :: 5 - Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Zope2",
        "Topic :: Internet :: WWW/HTTP :: Zope2 :: Product",
        ],
      keywords='web application server zope zope2',
      author="Zope Corporation and contributors",
      author_email="zope-cmf@lists.zope.org",
      url="http://www.zope.org/Products/GenericSetup",
      license="ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)",
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['Products'],
      zip_safe=False,
      #install_requires=['Zope >= 2.10']
      entry_points="""
      [zope2.initialize]
      Products.GenericSetup = Products.GenericSetup:initialize
      """,
      )
