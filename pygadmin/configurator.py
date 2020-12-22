import os
import yaml
import logging
import copy


class AppConfigurator:
    """
    Create a class for administration of the configuration file. The application has some options, which should be
    stored in a larger time delta than the runtime of the application. As a result, a .yaml file with configuration
    details exists, so there are configuration options stored. They can be edited with the use of a dictionary, which
    contains all the configuration options. This class can also handled cases with options, which are not set.
    """

    def __init__(self):
        # Define a path for the configuration files.
        configuration_path = os.path.join(os.path.expanduser("~"), '.pygadmin')

        # If the path for the configuration files does not exist, create it.
        if not os.path.exists(configuration_path):
            os.mkdir(configuration_path)

        # Define a configuration file.
        self.yaml_app_configuration_file = os.path.join(configuration_path, "app_configuration.yaml")
        self.yaml_editor_style_configuration_file = os.path.join(configuration_path, "editor_style.yaml")

        # Check for the existence of the configuration file.
        if not os.path.exists(self.yaml_app_configuration_file):
            # Create the file as an empty file for writing in it.
            open(self.yaml_app_configuration_file, "a")

        # Check for the existence of the editor configuration file.
        if not os.path.exists(self.yaml_editor_style_configuration_file):
            open(self.yaml_editor_style_configuration_file, "a")
            # Initialize default themes.
            self.init_default_themes()

        # Load the current data at the initialization of an object.
        self.load_configuration_data()

    def init_default_themes(self):
        """
        Create default themes for the style configuration and dump them in an empty file.
        """

        default_themes = {
            "Default": {"default_color": "ff000000",
                        "default_paper_color": "#ffffffff",
                        "keyword_color": "#ff00007f",
                        "number_color": "#ff007f7f",
                        "other_keyword_color": "#ff7f7f00",
                        "apostrophe_color": "#ff7f007f"},
            "Hack": {"default_color": "#59ff47",
                     "default_paper_color": "#141414",
                     "keyword_color": "#679cff",
                     "number_color": "#85fff7",
                     "other_keyword_color": "#ffe19b",
                     "apostrophe_color": "#f8bdff"},
            "Avocado": {"default_color": "#3a330a",
                        "default_paper_color": "#feffb3",
                        "keyword_color": "#68bd22",
                        "number_color": "#42ff9a",
                        "other_keyword_color": "#00ffc8",
                        "apostrophe_color": "#fff04a"}
        }

        try:
            with open(self.yaml_editor_style_configuration_file, "w") as default_theme_style_data:
                yaml.safe_dump(default_themes, default_theme_style_data)

        except Exception as file_error:
            logging.error("The file {} cannot be opened and default style information cannot be loaded with the "
                          "following error: {}".format(self.yaml_app_configuration_file, file_error), exc_info=True)

    def load_configuration_data(self):
        """
        Load the current data about the configuration in a dictionary out of the .yaml file for storing the
        configuration data.
        """

        # Use a try statement in case of a broken .yaml file.
        try:
            # Use the read mode for getting the content of the file.
            with open(self.yaml_app_configuration_file, "r") as connection_data:
                # Use the function for a safe load, because the file can be edited manually.
                self.configuration_dictionary = yaml.safe_load(connection_data)

            # Use the read mode for getting the content of the file.
            with open(self.yaml_editor_style_configuration_file, "r") as style_data:
                self.editor_style_dictionary = yaml.safe_load(style_data)

            self.check_data_load_for_empty_data()

            # Try to get the current command limit as check for its existence.
            try:
                self.configuration_dictionary["command_limit"]

            # If the current command limit does not exist, set it to a predefined value.
            except KeyError:
                # Set the command limit to 500.
                self.configuration_dictionary["command_limit"] = 500
                # Save the data in the configuration dictionary.
                self.save_configuration_data()

            # Try to find the current configuration for opening previous files.
            try:
                self.configuration_dictionary["open_previous_files"]

            # If the configuration does not exist, set the configuration to True and save the data.
            except KeyError:
                self.configuration_dictionary["open_previous_files"] = True
                self.save_configuration_data()

        except Exception as file_error:
            logging.error("The file {} cannot be opened and app configuration parameter cannot be loaded with the "
                          "following error: {}".format(self.yaml_app_configuration_file, file_error), exc_info=True)

    def check_data_load_for_empty_data(self):
        """
        Check the dictionary for the configurations and the styles for emptiness and assign them to an empty dictionary
        for None.
        """

        # If the loaded data is None, make an empty dictionary, so basic functions of the class can be used.
        if self.configuration_dictionary is None:
            self.configuration_dictionary = {}

        # If the loaded data is None, make an empty dictionary, so basic functions of the class can be used.
        if self.editor_style_dictionary is None:
            self.editor_style_dictionary = {}

    def save_configuration_data(self):
        """
        Save the data about the configuration in the .yaml file. This function should be used after a change of
        configuration parameters, which should be saved.
        """

        try:
            # Open the .yaml file in writing mode for dumping the data.
            with open(self.yaml_app_configuration_file, "w") as connection_data:
                yaml.safe_dump(self.configuration_dictionary, connection_data)

                # Report the success.
                return True

        except Exception as file_error:
            logging.error("The file {} cannot be opened and configurations cannot be saved with the following error:"
                          " {}".format(self.yaml_app_configuration_file, file_error))

    def get_single_configuration(self, configuration_to_check):
        """
        Get a single configuration parameter by its configuration key to check in the dictionary for all parameters.
        """

        # Try to find the key in the dictionary.
        try:
            # Get the value out of the dictionary.
            configuration_value = self.configuration_dictionary[configuration_to_check]

        # A KeyError happens, if the dictionary does not contain the given key.
        except KeyError:
            # Set the value to None, because there is None.
            configuration_value = None
            logging.info("Configuration information for {} is not set.".format(configuration_to_check))

        # Return the result, which is the actual result or None as "not found".
        return configuration_value

    def set_single_configuration(self, configuration_key, configuration_value):
        """
        Set a configuration with a configuration key and a configuration value. The name of the configuration key should
        be self-explaining, so it is understandable for a manual look in the .yaml file for configuration.
        """

        # Set the key and its value to the dictionary.
        self.configuration_dictionary[configuration_key] = configuration_value

    def delete_single_configuration(self, configuration_key):
        """
        Delete a single configuration specified by the configuration key out of the dictionary.
        """

        # Try to delete the given key out of the dictionary, because there is no further test, if the key is really part
        # of the dictionary.
        try:
            # Delete the key.
            del self.configuration_dictionary[configuration_key]

            # Return True for a success.
            return True

        # Catch a potential key error for a missing key in the dictionary.
        except KeyError:
            # Return False for a failure.
            return False

    def get_all_current_configurations(self):
        """
        Return the dictionary with all current configuration data.
        """

        # Return a copy of the dictionary.
        return copy.deepcopy(self.configuration_dictionary)

    def get_default_color_theme_style(self):
        """
        Get the current and default color theme style.
        """

        # Get the current color theme configuration.
        color_theme_configuration = self.get_single_configuration("color_theme")

        # Check fot the current content of the style dictionary.
        if self.editor_style_dictionary:
            # Find the match for the current configuration.
            for style_description, style_parameter in self.editor_style_dictionary.items():
                # If there is a match, return it.
                if style_description == color_theme_configuration:
                    return style_description, style_parameter

        # Return None for an empty editor style dictionary or a missing match in the dictionary.
        return None

    def add_style_configuration(self, style_name, style_parameter_in_dictionary):
        """
        Add a style configuration to the class-wide dictionary for all style configurations.
        """

        self.editor_style_dictionary[style_name] = style_parameter_in_dictionary

    def save_style_configuration_data(self):
        """
        Save the current style configuration data in a .yaml file for further usage after the runtime of one pygadmin.
        """

        try:
            # Open the .yaml file in writing mode for dumping the data.
            with open(self.yaml_editor_style_configuration_file, "w") as style_data:
                yaml.safe_dump(self.editor_style_dictionary, style_data)

                # Report the success.
                return True

        except Exception as file_error:
            logging.error("The file {} cannot be opened and database connection parameter cannot be saved with the "
                          "following error: {}".format(self.yaml_editor_style_configuration_file, file_error))

    def get_all_current_color_style_themes(self, load_new_data=True):
        """
        Load the current data out of the .yaml file for the newest and freshest and latest data. Return the style
        dictionary for all color styles.
        """

        # If new data is required (which is the default), load all the data again out of the .yaml files.
        if load_new_data:
            self.load_configuration_data()

        # Return a copy of the dictionary.
        return copy.deepcopy(self.editor_style_dictionary)


global_app_configurator = AppConfigurator()
