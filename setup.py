import os
from setuptools import setup
from setuptools import find_packages

NAME = 'GenericSetup'

here = os.path.abspath(os.path.dirname(__file__))
package = os.path.join(here, 'Products', NAME)
docs = os.path.join(here, 'docs')


def _package_doc(name):
    with open(os.path.join(package, name)) as f:
        return f.read()


def _docs_doc(name):
    with open(os.path.join(docs, name)) as f:
        return f.read()

with open('README.rst') as f:
    README = f.read()

_BOUNDARY = '\n' + ('-' * 60) + '\n\n'

CHANGES = _docs_doc('CHANGES.rst')

setup(
    name='Products.GenericSetup',
    version=_package_doc('version.txt').strip(),
    description='Read Zope configuration state from profile dirs / tarballs',
    long_description=README + _BOUNDARY + CHANGES,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "Framework :: Zope2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development",
        "Topic :: System :: Archiving :: Packaging",
        "Topic :: System :: Installation/Setup",
    ],
    keywords='web application server zope zope2 cmf',
    author="Zope Foundation and Contributors",
    author_email="zope-cmf@zope.org",
    url="https://pypi.python.org/pypi/Products.GenericSetup",
    license="ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)",
    packages=find_packages(),
    include_package_data=True,
    namespace_packages=['Products'],
    zip_safe=False,
    setup_requires=['eggtestinfo',
                    ],
    install_requires=[
        'setuptools',
        'Zope2 >= 2.12.3',
        'five.localsitemanager',
        # 'Products.MailHost', # BBB: disabled for Zope 2.12
        # 'Products.PythonScripts', # BBB: disabled for Zope 2.12
        ],
    tests_require=[
        'zope.testrunner',
        ],
    test_loader="zope.testrunner.eggsupport:SkipLayers",
    test_suite="Products.GenericSetup.tests",
    entry_points="""
    [zope2.initialize]
    Products.GenericSetup = Products.GenericSetup:initialize
    [distutils.commands]
    ftest = zope.testing.testrunner.eggsupport:ftest
    """,
    )
