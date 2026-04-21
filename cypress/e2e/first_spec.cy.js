before(() => {
    cy.ploneLoginAsRole("Manager");
    // Configure the Stripe processor
    cy.visit("http://localhost:8080/Plone/@@jazkarta-shop-settings");
    cy.getByLabel('Payment Processor').select('Stripe');
    cy.getByLabel('Stripe Secret Key (Development)').clear().type('foo');
    cy.getByLabel('Stripe Publishable Key (Development)').clear().type('foo');
    cy.getByLabel('Stripe Secret Key (Production)').clear().type('foo');
    cy.getByLabel('Stripe Publishable Key (Production)').clear().type('foo');
    cy.getByLabel('Receipt Email Introduction').clear().type('Thanks for your order');
    cy.getByLabel('Ship From Name').clear().type('A company');
    cy.getByLabel('Ship From Address').clear().type('Vendor street 101');
    cy.getByLabel('Ship From City').clear().type('A-city');
    cy.getByLabel('Ship From State').clear().type('A-state');
    cy.getByLabel('Ship From Zip').clear().type('00000');
    cy.contains("Save").click();
    // Configure the email for the site
    cy.visit("http://localhost:8080/Plone/@@mail-controlpanel");
    cy.getByLabel("Site 'From' name").clear().type('Jazkarta Shop');
    cy.getByLabel("Site 'From' address").clear().type('jazkarta.shop@example.com');
    cy.getByLabel("E-mail characterset").clear().type('utf-8');
    cy.contains("Save and send test e-mail").click();
    cy.contains("Success! Check your mailbox for the test message");
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
    it('buys one product', () => {
        cy.ploneLoginAsRole("Manager");
        createProduct({ title: 'Product 1', price: '10' });

        cy.intercept({
            method: 'POST',
            url: '/Plone/shopping-cart',
        }).as('updateCart');
        cy.contains("Add to cart").click();
        cy.wait('@updateCart').its('response.statusCode').should('equal', 200);
        cy.wait(500);

        cy.contains("My Cart").click();
        cy.contains("Checkout").click();
        cy.contains("Proceed to Checkout").click();
        cy.get("input[name=first_name]").type("John", { force: true });
        cy.get("input[name=last_name]").type("Doe", { force: true });
        cy.get("input[name=address]").type("Customer street 101", { force: true });
        cy.get("input[name=city]").type("Customer City", { force: true });
        cy.get("input[name=state]").type("Customer State", { force: true });
        cy.get("input[name=zip]").type("000000", { force: true });
        cy.get("input[name=email]").type("customer@example.com");
        cy.get("input[name=phone]").type("+1-555-555-5555");
        cy.contains("Cash").click();
        cy.contains("Complete Purchase").click();
        cy.contains("Thank You");
        cy.contains("Your purchases total");
        cy.contains("$10.00");
    })
})

const createProduct = function (options = {}) {
    const {
        title = 'Product',
        price = '5',
        description = 'A purchasable product',
    } = options;
    cy.visit("http://localhost:8080/Plone/++add++jazkarta.shop.product");
    cy.getByLabel('Title').type(title);
    cy.getByLabel('Summary').type(description);
    cy.contains("Shop").click();
    cy.getByLabel('Unit Price').clear().type(price);
    cy.contains("Save").click();
}
