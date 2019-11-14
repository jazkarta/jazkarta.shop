// Plone4 compatible version of shop.js

jQuery(function($){

    $(document).ready(function () {

        // update the cart details in the viewlet to avoid potential caching
        // issues for anon users
        $.get(portal_url + '/shopping-cart', function (data) {
            $('.jaz-shop-cart-wrapper').replaceWith(data);
        }, 'html');

        // update the cart details in the portlet via ajax to avoid potential
        // caching issues for anon users
        $.get(portal_url + '/@@jazkarta_shop_portletdata', function (data) {
            $('.jaz-shop-cart-portlet-wrapper').replaceWith(data);
        }, 'html');

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
            e.preventDefault();
            // Plone5 uses data-attributes which Plone4 does not recognize
            // add manual event handler to toggle the cart contents
            $('.jaz-shop-cart').toggle();
        });

        // hide portlet cart contents by clicking anywhere on page except my cart button
        $(document).mouseup(function (e){
	        var container = $(".jaz-shop-cart-portlet"); // contents
            var button = $('.jaz-shop-cart-portlet-trigger');
	        if ( !button.is(e.target) && (!container.is(e.target) && container.has(e.target).length === 0)) {
		        container.hide();
	        }
        });

        // click on my cart button
        $(document).on('click', '.jaz-shop-cart-portlet-trigger', function(e) {
            e.preventDefault();
            // Plone5 uses data-attributes which Plone4 does not recognize
            // add manual event handler to toggle the cart contents
            $('.jaz-shop-cart-portlet').toggle();
        });

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

        // update "Item"/"Items" via ajax to avoid potential caching issues for anon users
        $.get(portal_url + '/@@jazkarta_shop_portletdata?query=cart_items', function (data) {
                $('.jazkarta-shop-portlet-items').replaceWith(data);
        }, 'html');

    });

});
