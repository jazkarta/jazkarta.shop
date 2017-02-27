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

});
