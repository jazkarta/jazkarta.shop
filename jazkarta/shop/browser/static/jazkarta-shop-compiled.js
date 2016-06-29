require(['jquery'], function($) {

	var portal_url = $(body).data('portal-url');
    $(document).on('click', '.jaz-shop-add', function(e) {
        e.preventDefault();
        var uid = $(this).attr('data-uid');
        $.post(portal_url + '/shopping-cart', {'add': uid}, function(data) {
          $('.jaz-shop-cart-wrapper').replaceWith(data);
        }, 'html');
    });

});

define("/Users/davisagli/Work/jazkarta.com/src/jazkarta.shop/jazkarta/shop/browser/static/shop.js", function(){});

