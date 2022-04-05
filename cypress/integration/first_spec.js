before(() => {
    cy.ploneLoginAsRole("Manager");
    cy.visit("http://localhost:8080/Plone/prefs_install_products_form");
    cy.contains("jazkarta.shop").parent().within(() => {
        cy.contains("Install").click();
    });
    cy.contains("Installed jazkarta.shop!");
    cy.contains("Jazkarta Shop Settings").click()
});
describe('An order on a shop', () => {
    it('performs an order on the site', () => {
        console.log("foo")
    })
})
