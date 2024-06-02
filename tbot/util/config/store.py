import copy
from collections.abc import Mapping


class ConfigStore(Mapping):
    """Class to allow read-only access to fields of a dictionary.

    This class is intended to be used with configuration info for an application because it is often useful to access
    the info from various parts of a program.  It would be dangerous to allow any of those parts to modify the config, but
    it is often helpful to allow them to read it.
    """

    def __init__(self, init_data):
        """Initialize the ConfigStore.

        :param dict init_data: The configuration information to store as read-only. Presumably this comes from an init routine that first validated it
        """
        if not isinstance(init_data, dict):
            raise TypeError(
                f"The config data provided must be of type dict. Got {type(init_data)}"
            )

        self._data = copy.deepcopy(init_data)

    def __getitem__(self, key):
        """Return the item associated with the requested key.

        :param key: The config key to retrieve
        """
        return copy.deepcopy(self._data[key])

    def __iter__(self):
        """Return an iterator to the stored config data."""
        return iter(self._data)

    def __len__(self):
        """Return the number of key/value pairs in the top-level of the config store."""
        return len(self._data)
