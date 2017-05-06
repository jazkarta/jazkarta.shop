require(['jquery', 'mockup-utils'], function($, utils) {

    $(document).ready(function () {
        var portal_url = $('body').attr('data-portal-url');

        $.get(portal_url + '/shopping-cart', function (data) {
            $('.jaz-shop-cart-wrapper').replaceWith(data);
        }, 'html');

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

});
