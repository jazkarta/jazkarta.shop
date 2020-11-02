=============
jazkarta.shop
=============

A shopping cart and checkout for `Plone <http://plone.com>`_.

Compatible with:    
  * Plone 4.3
  * Plone 5.x on Python 2.7

Supports:  
  * Stripe
  * Authorize.net SIM (legacy)
  * Authorize.net Accept.js

Installation
============

Currently, there is no PYPI release, so the git repository has to be added to
a Plone buildout as a source. The following is a minimal example that will do
that and leave Plone ready to use jazkarta.shop.

Create a directory called Plone-5 and enter it::

    mkdir Plone-5
    cd Plone-5

Create a virtual python environment (virtualenv) and install zc.buildout::

    virtualenv-2.7 zinstance
    cd zinstance
    bin/pip install zc.buildout

Create a buildout.cfg file with the following contents::

    [buildout]
    extends =
        http://dist.plone.org/release/5-latest/versions.cfg

    parts =
        instance

    extensions =
        mr.developer

    always-checkout = force

    auto-checkout =
        jazkarta.shop

    [sources]
    jazkarta.shop = git git@github.com:jazkarta/jazkarta.shop.git

    [versions]
    # For python 2.7 compatibility
    premailer = 3.6.2
    cachetools = 3.1.1
    # Plone 5.1
    requests = 2.24

    [instance]
    recipe = plone.recipe.zope2instance
    user = admin:admin
    http-address = 8080
    eggs =
        Plone
        Products.validation
        Products.Archetypes
        Products.contentmigration
        archetypes.schemaextender
        jazkarta.shop

Change the `5-latest` version in the `extends` directive above to use a different
Plone version. This buildout should work on both 5.1 and 5.2 deployments.

Run buildout::

    ./bin/buildout

This will start a long download and build process.

You can ignore Errors like SyntaxError: ("'return' outside function"...".

After it finished you can start Plone in foreground-mode with::

    ./bin/instance fg

You can stop it with ctrl + c.

Start and stop this Plone-instance in production-mode like this::

    ./bin/instance start

    ./bin/instance stop

Plone will run on port 8080. You can access your install via http://localhost:8080.

Use login id “admin” and password “admin” for initial login so you can create a site.


Integrating the Package with Your Content
=========================================

To make your content types addable to your cart, implementing the IProduct interface is required::

    from jazkarta.shop.interfaces import IProduct

    class Journal(Container):
         implements(IJournal, IProduct)

Credits
=======

Built by Jazkarta.
