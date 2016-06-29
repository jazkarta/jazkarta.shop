require(['jquery', 'mockup-utils'], function($, utils) {

	var portal_url = $('body').data('portal-url');
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

});
