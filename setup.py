from setuptools import setup, find_packages

version = '2.0.3'

setup(
    name='jazkarta.shop',
    version=version,
    description="Web-based shop for Plone",
    long_description=open("README.rst").read(),
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 5.1",
        "Framework :: Plone :: 5.2",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords='ecommerce',
    author='Jazkarta',
    author_email='info@jazkarta.com',
    url='http://github.com/jazkarta/jazkarta.shop',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['jazkarta'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'authorizenet',
        'collective.z3cform.datagridfield',
        'stripe~=2.56',
        'premailer',
        'python-ups; python_version<"3"',
        'requests[security]',
        'z3c.currency',
        'plone.protect>=3.0.19', # Plone 4.3.11 ships with 2.0.3. Version 3.0.9+
                                 # required for plone.protect.utils.safeWrite
                                 # Version 3.0.19 required for inclusion of
                                 # protect.js from plone4.csrffixes
        'plone.api',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
        ],
    },
    entry_points="""
    # -*- Entry points: -*-
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
