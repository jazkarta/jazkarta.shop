require(['jquery', 'mockup-utils'], function($, utils) {

    if ( $('body').hasClass('template-review-cart') ) {
        // hide my cart on the review-cart view to prevent 
        // potential inconsistencies if the cart is updated in this view
        $('.jaz-shop-cart-wrapper').hide()
    }
    else {
        $('.jaz-shop-cart-wrapper').show()
	    var portal_url = $('body').attr('data-portal-url');
        $(document).on('click', '.jaz-shop-add', function(e) {
            e.preventDefault();
            var uid = $(this).attr('data-uid');
            $.post(portal_url + '/shopping-cart', {
            	'add': uid,
            	'_authenticator': utils.getAuthenticator()
            }, function(data) {
              $('.jaz-shop-cart-wrapper').replaceWith(data);
            }, 'html');
        });
    }
});
