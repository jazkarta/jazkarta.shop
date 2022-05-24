=============
jazkarta.shop
=============

An e-commerce shopping cart and checkout for `Plone <http://plone.com>`_, optimized for use in the US and Canada.

Features
========

Shopping Cart
-------------

Users can add items to their cart while browsing products on the website. They can then click the cart icon to view 
and adjust the contents of their shopping cart.

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
- UPS (Python 2.x only)

Pluggable Sales Tax APIs
------------------------

For calculating US state and local taxes. Currently available:

- Washington state handler
- Taxjar handler (a commercial service for automated sales tax calculation based on address) 
- NoTax handler for disabling sales tax calculation entirely

Purchasable Content Types
-------------------------

Types can be Dexterity or Archetypes. Make your own content type purchasable using a behavior or schema extender.
(Note: Archetypes support in Python 2.x only)

Recommended products
--------------------

A product can have other products related to it so that they can be recommended at the time of purchase. When users review their cart, they will be presented with a list of recommended products populated from the Recommended Products fields of all the products they're about to purchase.

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
- Plone 5.2.x on Python 2.7, 3.6, 3.7, 3.8

Translations
============

This product has been translated into

- English (U.S.)

Installation
============

Install jazkarta.shop by adding it to your buildout::

    [buildout]
    
    ...
    
    eggs =
        jazkarta.shop


and then running::

    bin/buildout

Integrating the Package with Your Content
=========================================

Add the "Jazkarta Shop Product" Dexterity behavior to each content type that you wish to use with jazkarta.shop,
either through the web or programmatically in your code. 

To add the schema extender on Archetypes content types,  programmatically implement the 
interface ``jazkarta.shop.interfaces.IATProduct`` on your content class or otherwise provide the interface 
on individual instances.

When creating instances of your content type, make sure to set the weight and unit price on each one. 
This is will appear under the "Shop" fieldset when adding/editing your object.

Minimal configuration/Quickstart
================================

Proceed to the "Jazkarta Shop Settings" to configure a payment processor, optional shipping method API keys, 
shipped from address details as well as a recepit email message.

Proceed to the "Jazkarta Shop Shipping Methods" to setup a shipping method.
Destinations are grouped by shipping zones
"Alaska, Canada, East, Hawaii, International, Midwest, US, West"

It is important to select at least one shipping zone for your shipping method(s) to show up once the 
shipping address has been entered during the checkout process.

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

If using UPS or USPS shipping methods, please make sure the revelevant API keys are added in the "Jazkarta Shop Settings" control panel.

Jazkarta Shop Orders
--------------------

This control panel provides a table of order information such as date, items, shipping information and price.

Future Work
===========

Promo Codes
-------------
Promotional codes for discounts can be defined and applied to a shopping cart.
Currently a promo code widget is visible on the Shopping cart (review-cart) view, however this functionality is not complete.

Contribute
==========

- Issue Tracker: https://github.com/jazkarta/jazkarta.shop/issues
- Source Code: https://github.com/jazkarta/jazkarta.shop

License
=======

The project is licensed under the GPLv2.

Credits
=======

Built by `Jazkarta <https://jazkarta.com>`_.

Authors
-------

- David Glick (initial author)
- Carlos de la Guardia
- Alec Mitchell
- Witek
- Fulvio Casali
- Silvio Tomatis
- Alessandro Ceglie
