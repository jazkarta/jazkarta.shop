Changelog
=========

2.0.4 (2022-05-04)
-----------------

- Don't render recommended products when there aren't any.

2.0.3 (2022-04-21)
-----------------

- Fix issue with recommended product rendering on custom AT products.

2.0.2 (2022-04-08)
-----------------

- Fix Python 2.7 compatibility issue


2.0.1 (2022-04-08)
-----------------

First public release incorporates the following features and fixes:

- Support for recommended products in cart view

- using Pickadate pattern to choose dates in @@jazkarta-shop-orders

- Python 3 support, (Archetypes and UPS shipping support for python 2.x only)

- Stripe elements support

- Authorize.net SIM is deprecating the use of MD5.
  Added support for the the SHA512 that replaces it
  (requires the signature key is specified)

- Refactored checkout forms into separate modules

- Added support for checkout using Authorize.net Accept.js

- Cart now implements `add_item` for adding an item
  that isn't based on a content item.

- Cart now implements `__del__` for removing items.

- Avoid breaking if a cart item is missing its price.

- Default to looking up product using resolve_uid
  if purchase handler doesn't implement get_obj_href.

- Wrap scripts in a div with id="stripe" to facilitate moving it with Diazo.

- Get browser id manager directly to avoid breaking when using
  BeakerSessionDataManager.

- Trigger a CheckoutComplete event after checkout is complete
  and order has been recorded.
