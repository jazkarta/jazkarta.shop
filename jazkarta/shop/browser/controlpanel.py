from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.registry.interfaces import IRegistry
from plone.z3cform import layout
from zope.component import getUtility
from ..interfaces import ISettings


class SettingsControlPanelForm(RegistryEditForm):
    schema = ISettings

    def update(self):
        # Make sure we have registry records for all the fields
        registry = getUtility(IRegistry)
        registry.registerInterface(ISettings)

        super(SettingsControlPanelForm, self).update()


SettingsControlPanelView = layout.wrap_form(
    SettingsControlPanelForm, ControlPanelFormWrapper)
SettingsControlPanelView.label = u"Jazkarta Shop Settings"
