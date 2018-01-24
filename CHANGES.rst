Changelog

- Cart now implements `__del__` for removing items.

- Avoid breaking if a cart item is missing its price.

- Default to looking up product using resolve_uid
  if purchase handler doesn't implement get_obj_href.

- Wrap scripts in a div with id="stripe" to facilitate moving it with Diazo.

- Get browser id manager directly to avoid breaking when using
  BeakerSessionDataManager.

- Trigger a CheckoutComplete event after checkout is complete
  and order has been recorded.
