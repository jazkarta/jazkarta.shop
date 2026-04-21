from zope.i18nmessageid import MessageFactory
_ = MessageFactory('jazkarta.shop')

import logging
logger = logging.getLogger('jazkarta.shop')


# Patch plone.z3cform.fieldsets.utils.add for a Py3 bug where odict_keys is
# sliced. Fixed upstream in plone.z3cform 2.x, which does not work with Plone
# 5.2. This fixes TypeError on Python 3 when rendering add forms using
# model.fieldset().
def _patch_plone_z3cform():
    from plone.z3cform.fieldsets import utils
    from plone.z3cform.fieldsets.group import GroupFactory
    from z3c.form.field import Fields
    import six

    if getattr(utils.add, '_jazkarta_shop_patched', False):
        return

    orig_add = utils.add

    def add(form, *args, **kwargs):
        try:
            return orig_add(form, *args, **kwargs)
        except TypeError:
            pass
        # Upstream slices odict_keys as if it were a list. Reimplement the
        # insertion branch with list(keys()) to preserve the requested index.
        index = kwargs.pop('index', None)
        group = kwargs.pop('group', None)
        new_fields = Fields(*args, **kwargs)
        if not group or isinstance(group, six.string_types):
            source = utils.find_source(form, group=group)
        else:
            source = group
        if source is None and group:
            source = GroupFactory(group, new_fields)
            form.groups.append(source)
        else:
            field_names = list(source.fields.keys())
            source.fields = source.fields.select(*field_names[:index]) + \
                new_fields + \
                source.fields.select(*field_names[index:])

    add._jazkarta_shop_patched = True
    utils.add = add


try:
    _patch_plone_z3cform()
except Exception:
    logger.exception('Could not patch plone.z3cform.fieldsets.utils.add')
