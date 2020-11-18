import os
import logging.config
import yaml


def setup_logging_configuration(configuration_file_path="logging.yaml", configuration_level=logging.INFO,
                                environment_key="LOG_CFG"):

    """
    Check for an existing configuration file logging.yaml, which contains the configuration for logging, and use it, if
    it exists. Use a default, basic configuration, if it does not exist.
    """

    # Get environment variable based on the given key.
    environment_value = os.getenv(environment_key, None)

    # If the environment value exists, use it as path.
    if environment_value:
        configuration_file_path = environment_value

    # If there is a configuration path with an existing file, use it.
    if os.path.exists(configuration_file_path):
        # Open the configuration in read and text mode, which is necessary for the yaml functionality.
        with open(configuration_file_path, "rt") as configuration_file:
            # Read the configuration file with the yaml function for safe load. This is necessary because a user can
            # change their configuration.
            configuration = yaml.safe_load(configuration_file.read())

        # Take the configuration information out of the created dictionary.
        logging.config.dictConfig(configuration)

    else:
        # If a configuration file is not found, make a simple output.
        logging.basicConfig(level=configuration_level)
        # Use logging to inform the user about insufficient logging.
        logging.warning("A configuration file was not found in the path {}. .log files will not be "
                        "produced. Please check your logging settings and configuration "
                        "file".format(configuration_file_path))

