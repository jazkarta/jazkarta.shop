=============
jazkarta.shop
=============

An e-commerce shopping cart and checkout for `Plone <http://plone.com>`_.

Features
========

Shopping Cart
-------------

Users can add items to their cart while browsing products on the website. They can then click the cart icon to view and adjust the contents of their shopping cart.

Pluggable Payment Processors
----------------------------

Currently available:

- Stripe (Stripe Elements)
- Authorize.net SIM (legacy)
- Authorize.net Accept.js

Pluggable Shipping Providers
----------------------------

Currently available:

- USPS 
- UPS

Pluggable Sales Tax APIs
------------------------

For calculating US state and local taxes. Currently available:

- Washington state handler
- Taxjar handler (a commercial service for automated sales tax calculation based on address) 
- NoTax handler for disabling sales tax calculation entirely

Purchasable Content Types
-------------------------

Types can be Dexterity or Archetypes. Make your own content type purchasable using a behavior or schema extender.

Cart Stored in ZODB
------------------------

Shopping cart data is stored in the ZODB rather than in sessions even for anonymous users. This makes it easier to deploy when running multiple Zope instances.

PloneFormGen Integration
------------------------

Provided by jazkarta.pfg.jazshop.
  
Compatible With
---------------

- Plone 4.3
- Plone 5.0.x, 5.1.x on Python 2.7
- Plone 5.2.x on Python 2.7, 3.6, 3.7

Installation
============

Currently, there is no PYPI release, so the git repository has to be added to
a Plone buildout as a source. The following is a minimal example that will do
that and leave Plone ready to use jazkarta.shop.

Create a directory called Plone-5 and enter it::

    mkdir Plone-5
    cd Plone-5

Create a virtual python environment (virtualenv) and install zc.buildout::

    virtualenv zinstance --python=python2.7
    cd zinstance
    source bin/activate
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
    cryptography=3.3.2
    cssutils=1.0.2

    setuptools=44.1.1
    zc.buildout=2.13.4

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

Change the version pin of zc.buildout and setuptools to match the version that running bin/pip command pulled in, eg:

    Using cached zc.buildout-2.13.4-py2.py3-none-any.whl (153 kB)
    Requirement already satisfied: setuptools<52,>=8.0 in ./lib/python2.7/site-packages (from zc.buildout) (44.1.1)


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

Add the "Jazkarta Shop Product" dexterity behavior to each content type that you wish to use with jazkarta.shop,
either through the web or programatically in your code.

When creating instances of your content type, make sure to set the weight and unit price on each one. This is will appear under the "Shop" fieldset when adding/editing your object.


Minimal configuration/Quickstart
================================

Proceed to the "Jazkarta Shop Settings" to configure a payment processor, optional shipping method api keys, shipped from address details as well as a recepit email message.

Proceed to the "Jazkarta Shop Shipping Methods" to setup a shipping method.
Destinations are grouped by shipping zones
"Alaska, Canada, East, Hawaii, International, Midwest, US, West"

It is important to select at least one shipping zone for your shipping method(s) to show up once the shipping address has been entered during the checkout process.

Currently available zones can be seen in detail here::

    WEST = {
        'AZ', 'CA', 'CO', 'ID', 'MT', 'NV', 'NM', 'OR', 'UT', 'WY', 'WA'
    }

    MIDWEST = {
        'AL', 'AR', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'MI', 'MN', 'MS',
        'MO', 'NE', 'ND', 'OH', 'OK', 'SD', 'TN', 'TX', 'WI',
    }

    EAST = {
        'CT', 'DE', 'FL', 'GA', 'ME', 'MD', 'MA', 'NH', 'NJ', 'NY', 'NC',
        'PA', 'RI', 'SC', 'VT', 'VA', 'WV'
    }


Administration
==============

Three control panels are provided.

Jazkarta Shop Settings
----------------------

This control panel allows configuration of:

- Which payment processor to use
- Payment processor keys or login information for development and production use
- Subject and introduction for receipt emails
- Product categories
- Minimum stock level
- Shipped from name and address
- Shipping handler keys or login information
- Which tax handler to use
- Optional Taxjar API token
- Optional after-checkout callback URL

jazkarta.shop requires the environment variable ``JAZKARTA_SHOP_ENV`` to be set to ``production`` when it is running in production mode.

Jazkarta Shop Shipping Methods
------------------------------

Named shipping methods can be added and edited. Each shipping method specifies the geographical areas it is used for, the shipping fee calculation method, minimum and maximum weights, and optionally a minimum purchase amount.

If using UPS or USPS shipping methods, please make sure the revelevant api keys are added in the "Jazkarta Shop Settings" control panel.

Jazkarta Shop Orders
--------------------

This control panel provides a table of order information such as date, items, shipping information and price.


Future Work
===========

Promo Codes
-------------
Promotional codes for discounts can be defined and applied to a shopping cart.
Currently a promo code widget is visible on the Shopping cart (review-cart) view, however this functionality is not complete


Credits
=======

Built by Jazkarta.

Authors
-------

- David Glick (initial author)
- Carlos de la Guardia
- Alec Mitchell
- Witek
- Fulvio Casali

