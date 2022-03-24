from BTrees.OOBTree import OOBTree
from jazkarta.shop import config
from .utils import get_site


def get_storage(for_write=False):
    site = get_site()
    if for_write and not hasattr(site, config.STORAGE_KEY):
        setattr(site, config.STORAGE_KEY, OOBTree())
    return getattr(site, config.STORAGE_KEY, {})


def get_shop_data(path, default=None):
    storage = get_storage()
    for key in path[:-1]:
        storage = storage.get(key, {})
    return storage.get(path[-1], default)


def set_shop_data(path, value):
    storage = get_storage(for_write=True)
    for key in path[:-1]:
        if key not in storage:
            storage[key] = OOBTree()
        storage = storage[key]
    storage[path[-1]] = value


def del_shop_data(path):
    storage = get_storage(for_write=True)
    for key in path[:-1]:
        # We couldn't find a parent key, bail
        if key not in storage:
            return
        storage = storage[key]
    key = path[-1]
    if key in storage:
        del storage[key]
    # If the parent has no remaining keys, delete it too
    if len(storage.keys()) == 0 and len(path) > 1:
        del_shop_data(path[:-1])


def increment_shop_data(path, delta):
    storage = get_storage(for_write=True)
    for key in path[:-1]:
        if key not in storage:
            storage[key] = OOBTree()
        storage = storage[key]
    key = path[-1]
    if key not in storage:
        storage[key] = 0
    storage[key] += 1
