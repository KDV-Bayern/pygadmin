import unittest
import os

from pygadmin.configurator import global_app_configurator


class TestConfiguratorMethods(unittest.TestCase):
    """
    Test the app configurator with its methods and behavior.
    """

    def test_path_of_configuration_files(self):
        """
        Test the existence of the two file paths.
        """

        # Get the path for the general configuration file and test it.
        configuration_file = global_app_configurator.yaml_app_configuration_file
        assert os.path.exists(configuration_file)

        # Get the path for the editor style configuration file and test it.
        editor_style_file = global_app_configurator.yaml_editor_style_configuration_file
        assert os.path.exists(editor_style_file)

    def test_configuration_dictionary(self):
        """
        Test the correct load of the configuration dictionary.
        """

        assert global_app_configurator.configuration_dictionary is not None
        assert isinstance(global_app_configurator.configuration_dictionary, dict)

    def test_style_configuration_dictionary(self):
        """
        Test the correct load of the editor style dictionary.
        """

        assert global_app_configurator.editor_style_dictionary is not None
        assert isinstance(global_app_configurator.editor_style_dictionary, dict)

    def test_save_configuration_data(self):
        """
        Test the save of all current configuration data, which should return True for a success.
        """

        assert global_app_configurator.save_configuration_data() is True

    def test_save_style_data(self):
        """
        Test the save of all current style data, which should return True for a success.
        """

        assert global_app_configurator.save_style_configuration_data() is True

    def test_get_all_current_configurations(self):
        """
        Test getting all current configurations. The result should be a dict.
        """

        assert isinstance(global_app_configurator.get_all_current_configurations(), dict)

    def test_get_all_current_style_themes(self):
        """
        Test getting all current style themes and the correct structure of the returning dictionary.
        """

        # Get the style dictionary.
        style_dictionary = global_app_configurator.get_all_current_color_style_themes()

        # Test for the right instance.
        assert isinstance(style_dictionary, dict)

        # Test every value in the dictionary for the correct instance, which should also be a dictionary.
        for value in style_dictionary.values():
            assert isinstance(value, dict)

    def test_set_single_configuration(self):
        """
        Set a single configuration and test for correct setting with direct access to the dictionary.
        """

        # Define a key and a value for testing.
        test_key = "test"
        test_value = True

        # Set the configuration.
        global_app_configurator.set_single_configuration(test_key, test_value)
        # Get the value to the key with direct access to the dictionary.
        assert global_app_configurator.configuration_dictionary[test_key] is test_value

    def test_get_single_configuration(self):
        """
        Set a single configuration and test for the correct setting and getting with the method of the app configurator.
        """

        # Define a test key and a test value.
        test_key = "test"
        test_value = True

        # Set the configuration.
        global_app_configurator.set_single_configuration(test_key, test_value)
        # Get the value to the key with the method of the app configurator.
        assert global_app_configurator.get_single_configuration(test_key) is test_value

    def test_delete_configuration(self):
        """
        Set a configuration and delete the configuration again for testing the correct deletion. Test also the case for
        a non existing configuration.
        """

        # Define a test key and a test value.
        test_key = "test"
        test_value = True

        # Set the configuration.
        global_app_configurator.set_single_configuration(test_key, test_value)
        # Delete the configuration based on its key and check if the result is True for a successful deletion.
        assert global_app_configurator.delete_single_configuration(test_key) is True
        # Delete the configuration based on its key again, which should fail, so the result is False.
        assert global_app_configurator.delete_single_configuration(test_key) is False

    def test_get_all_configurations(self):
        """
        Test to get all components and check the correctness with direct access.
        """

        configurations = global_app_configurator.get_all_current_configurations()
        assert configurations == global_app_configurator.configuration_dictionary

    def test_default_color_theme(self):
        """
        Test to get the default color theme.
        """

        # Get the color theme out of the global app configurator.
        color_theme = global_app_configurator.get_single_configuration("color_theme")

        # Proceed, if the editor style dictionary and the color theme is not None. So there are elements in the style
        # dictionary and there is a color theme.
        if global_app_configurator.editor_style_dictionary and color_theme:
            # Get the style description and the style values (as a dictionary).
            style_description, style_values = global_app_configurator.get_default_color_theme_style()
            # The first value should be the color theme,
            assert style_description == color_theme
            # The second value should contain a dictionary with the different color themes.
            assert isinstance(style_values, dict)

        # If the color theme or the style dictionary (or both) is None or empty, the result for the default color theme
        # should also be None.
        else:
            assert global_app_configurator.get_default_color_theme_style() is None

