before(() => {
    cy.ploneLoginAsRole("Manager");
    cy.visit("http://localhost:8080/Plone/dexterity-types/Document/@@behaviors");
    cy.get('input[name="form.widgets.jazkarta.shop.interfaces.IProduct:list"]').check();
    cy.get('input[name="form.widgets.jazkarta.shop.interfaces.IRelatedProducts:list"]').check();
    cy.contains("Save").click();
});
describe('Admin operations', () => {
    it('can view an empty order list', () => {
        cy.visit("http://localhost:8080/Plone/@@jazkarta-shop-orders");
    })
})
