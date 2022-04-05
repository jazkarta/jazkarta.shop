before(() => {
    cy.ploneLoginAsRole("Manager");
    cy.visit("http://localhost:8080/Plone/dexterity-types/Document/@@behaviors");
    cy.get('input[name="form.widgets.jazkarta.shop.interfaces.IProduct:list"]').check();
    cy.get('input[name="form.widgets.jazkarta.shop.interfaces.IRelatedProducts:list"]').check();
    cy.contains("Save").click();
    // cy.contains("Jazkarta Shop Settings").click()
});
describe('An order on a shop', () => {
    it('performs an order on the site', () => {
        console.log("foo")
    })
})
