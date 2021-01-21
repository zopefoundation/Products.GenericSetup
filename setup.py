import os

from setuptools import find_packages
from setuptools import setup


NAME = 'GenericSetup'
URL = 'https://github.com/zopefoundation/Products.%s' % NAME

here = os.path.abspath(os.path.dirname(__file__))
package = os.path.join(here, 'src', 'Products', NAME)
docs = os.path.join(here, 'docs')


def _package_doc(name):
    with open(os.path.join(package, name)) as f:
        return f.read()


with open('README.rst') as f:
    README = f.read()

with open('CHANGES.rst') as f:
    CHANGES = f.read()

_BOUNDARY = '\n' + ('-' * 60) + '\n\n'

setup(
    name='Products.GenericSetup',
    version=_package_doc('version.txt').strip(),
    description='Read Zope configuration state from profile dirs / tarballs',
    long_description=README + _BOUNDARY + CHANGES,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone :: 5.2",
        "Framework :: Zope :: 4",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development",
        "Topic :: System :: Archiving :: Packaging",
        "Topic :: System :: Installation/Setup",
    ],
    keywords='web application server zope zope4 cmf',
    author="Zope Foundation and Contributors",
    author_email="zope-cmf@zope.org",
    url=URL,
    project_urls={
        'Documentation': 'https://productsgenericsetup.readthedocs.io',
        'Source code': URL,
        'Issue tracker': '%s/issues' % URL,
    },
    license="ZPL 2.1",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['Products'],
    zip_safe=False,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
    install_requires=[
        'setuptools',
        'six',
        'Zope >= 4.0b4',
        'five.localsitemanager',
        'Products.PythonScripts',
        'Products.ZCatalog',
    ],
    extras_require=dict(
        docs=['Sphinx', 'repoze.sphinx.autointerface'],
    ),
    entry_points="""
    [zope2.initialize]
    Products.GenericSetup = Products.GenericSetup:initialize
    """,
)
