before(() => {
    cy.ploneLoginAsRole("Manager");
    cy.visit("http://localhost:8080/Plone/dexterity-types/Document/@@behaviors");
    cy.get('input[name="form.widgets.jazkarta.shop.interfaces.IProduct:list"]').check();
    cy.contains("Save").click();
});
describe('Admin operations', () => {
    it('can view an empty order list', () => {
        cy.ploneLoginAsRole("Manager");
        cy.visit("http://localhost:8080/Plone/@@jazkarta-shop-orders");
    })
    it('creates a buyable product', () => {
        cy.ploneLoginAsRole("Manager");
        createProduct({ title: 'Product', price: '10' });
    })
    it('creates two related buyable products', () => {
        cy.ploneLoginAsRole("Manager");
        createProduct({ title: 'Product 1', price: '10' });
        createProduct({ title: 'Product 2', price: '50' });
    })
})

const createProduct = function (options = {}) {
    const {
        title = 'Product',
        price = '5',
        description = 'A purchasable product',
        text = 'You can buy me!'
    } = options;
    cy.visit("http://localhost:8080/Plone/++add++Document");
    cy.getByLabel('Title').type(title);
    cy.getByLabel('Summary').type(description);
    getIframeBody('IRichTextBehavior-text').type(text)
    cy.contains("Shop").click();
    cy.getByLabel('Unit Price').clear().type(price);
    cy.contains("Save").click();
}


const getIframeDocument = (fieldName) => {
    return cy
        .get(`#formfield-form-widgets-${fieldName} iframe`)
        // Cypress yields jQuery element, which has the real
        // DOM element under property "0".
        // From the real DOM iframe element we can get
        // the "document" element, it is stored in "contentDocument" property
        // Cypress "its" command can access deep properties using dot notation
        // https://on.cypress.io/its
        .its('0.contentDocument').should('exist')
}

const getIframeBody = (fieldName) => {
    // get the document
    return getIframeDocument(fieldName)
        // automatically retries until body is loaded
        .its('body').should('not.be.undefined')
        // wraps "body" DOM element to allow
        // chaining more Cypress commands, like ".find(...)"
        .then(cy.wrap)
}