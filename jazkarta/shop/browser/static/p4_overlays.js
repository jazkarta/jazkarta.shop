jQuery(function($){

    $('a.p4-modal').prepOverlay({
        subtype: 'ajax',
        filter: '#content>*',
        noform: 'reload',
        redirect: location.href,
        });
});
