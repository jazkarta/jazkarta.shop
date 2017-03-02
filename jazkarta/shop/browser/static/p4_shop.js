// Plone4 compatible version of shop.js

jQuery(function($){

    $(document).on('click', '.jaz-shop-add', function(e) {
        e.preventDefault();
        var uid = $(this).attr('data-uid');
        $.post(portal_url + '/shopping-cart', {
        	'add': uid
        }, function(data) {
          $('.jaz-shop-cart-wrapper').replaceWith(data);
        }, 'html');
    });

    $(document).on('click', '.jaz-shop-cart-trigger', function(e) {
        // Plone5 uses data-attributes which Plone4 does not recognize
        // add manual event handler to toggle the cart contents
        $('.jaz-shop-cart').toggle();
    });

});
