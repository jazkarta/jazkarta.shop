from setuptools import setup, find_packages

version = '1.0.dev0'

setup(
    name='jazkarta.shop',
    version=version,
    description="Web-based shop for Plone",
    long_description=open("README.rst").read(),
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Framework :: Plone :: 5.0",
        "Programming Language :: Python",
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
        'collective.z3cform.datagridfield',
        'stripe',
        'premailer',
        'python-ups',
        'requests',
        'z3c.currency',
        'plone.protect>=3.0.9', # Plone 4.3.11 ships with 2.0.3. Version 3.0.9+
                                # required for plone.protect.utils.safeWrite
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
