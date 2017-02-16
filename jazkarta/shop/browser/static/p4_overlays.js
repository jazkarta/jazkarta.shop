function Plone4PrepOverlay() {
    $('a.p4-modal').prepOverlay({
        subtype: 'ajax',
        filter: '#content>*',
        formselector: '#form',
        noform: 'reload',
        redirect: location.href,
        closeselector: '[name=form.buttons.Cancel]'
        });
}
