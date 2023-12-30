import sys

import yaml
from schema import SchemaError

from .store import ConfigStore

# Do not reference these global variables directly
_default_config = None
_named_configs = dict()


def _parse_yaml(filepath):
    with open(filepath.resolve(), "r") as yaml_file:
        result = yaml.safe_load(yaml_file)
        if result is None:
            raise ValueError(f"File {filepath} does not contain valid YAML.")
        return result


def _store_config(config_name, config_d):
    global _default_config
    global _named_configs

    # If name is None, try to store the config as the default
    if config_name is None:
        if _default_config is not None:
            raise ValueError(
                "Default config has already been set. Try giving this config a config_name."
            )
        else:
            _default_config = ConfigStore(config_d)

    # Store the config under the name key
    else:
        if config_name in _named_configs:
            raise ValueError(f"A config with config_name {config_name} already exists.")
        else:
            _named_configs[config_name] = ConfigStore(config_d)


def load_yaml_file(filepath):
    """Attempt to load a YAML config from the provided filepath.

    :param pathlib.Path filepath: Path to the file

    On success this function throws no exceptions.

    This function may fail with
      * FileNotFoundError if the YAML file could not be loaded from the provided path
      * ValueError if the file does not contain YAML
      * ValueError if config_name is None, but there is already a default config
    """
    with open(filepath.resolve(), "r") as yaml_file:
        result = yaml.safe_load(yaml_file)
        if result is None:
            raise ValueError(f"File {filepath} does not contain valid YAML.")
        return result


def validate_schema(cfg, schema, config_name=None):
    """Attempt to load a YAML config from the provided filepath.

    :param dict cfg: A dictionary containing the config to validate
    :param schema.Schema schema: The full schema to validate the yaml file against
    :param str config_name: The name/key to give to this config. If None, this will become the default config
    """
    # The author of the Schema library has some really weird way of catching and re-throwing an exception when the
    # schema fails to validate.  There is no way to return ALL validation errors, so I chose to return the first error
    # in a way that's legible to the user.
    validation_error = None
    try:
        schema.validate(cfg)
        _store_config(config_name, cfg)

    except SchemaError:
        # What happens is that the first SchemaError triggers another SchemaError inside of an exception handler.
        # Then it causes the traceback to append the messages together, producing a massive wall of text for a simple
        # error message.  This is worked around here by recreating the SchemaError from just the original validation error.
        validation_error = SchemaError(str(sys.exc_info()[1]))

    # Raising the exception outside of the handler stops us from getting the daisy-chained traceback
    if validation_error:
        raise validation_error


def get(config_name=None):
    """Attempt to retrieve a config based on the provided key.

    :param str config_name: The name of the config to retrieve. If config_name is None, the default config is retrieved.
    :returns ConfigStore: The config associated with config_name, or None if one isn't found.
    """
    if not config_name:
        return _default_config

    else:
        return _named_configs.get(config_name, None)
