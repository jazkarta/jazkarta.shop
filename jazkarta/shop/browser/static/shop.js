require(['jquery', 'mockup-utils'], function($, utils) {

    $(document).ready(function () {
        var portal_url = $('body').attr('data-portal-url');

        // update the cart details in the viewlet to avoid potential caching
        // issues for anon users
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

        // update the cart details in the portlet via ajax to avoid potential
        // caching issues for anon users
        $.get(portal_url + '/@@jazkarta_shop_portletdata', function (data) {
            $('.jaz-shop-cart-portlet-wrapper').replaceWith(data);
        }, 'html');

        // update the number of items in the portlet via ajax to avoid potential
        // caching issues for anon users
        // also hide the entire portlet if it contains no items
        $.get(portal_url + '/@@jazkarta_shop_portletdata?query=cart_size', function (data) {
            if (data == '0') {
                $('.jazkarta-cart-portlet').hide();
            }
            else {
                $('.jazkarta-cart-portlet').show();
                $('.jazkarta-shop-portlet-cartsize').replaceWith(data);
            }
        }, 'html');

    });

});
