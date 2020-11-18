import unittest
import sys

from PyQt5.QtWidgets import QApplication, QDialog, QCheckBox, QLineEdit

from pygadmin.configurator import global_app_configurator
from pygadmin.widgets.configuration_settings import ConfigurationSettingsDialog


class TestConfigurationSettingsDialogMethods(unittest.TestCase):
    """
    Test the functionality and methods of the configuration settings dialog.
    """

    def test_initial_attributes(self):
        """
        Test the correct class and the initial attributes of the configuration settings dialog.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create an dialog.
        configuration_settings_dialog = ConfigurationSettingsDialog()
        # Check the correct instance.
        assert isinstance(configuration_settings_dialog, QDialog)
        # Check for the correct instance of the configuration dictionary.
        assert isinstance(configuration_settings_dialog.configuration_dictionary, dict)

    def test_save_current_configuration(self):
        """
        Test the save of the current configuration: Check the text or check box status of the GUI elements and their
        correct save in the dictionary.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        configuration_settings_dialog = ConfigurationSettingsDialog()

        # The function should return True for a success.
        assert configuration_settings_dialog.save_current_configuration() is True

        # Check the correct save of every user input.
        for description, gui_elements in configuration_settings_dialog.configuration_dictionary.items():
            # The dialog shows the configurations in a more readable version.
            description = description.replace(" ", "_")
            # Get the current configuration.
            configuration = global_app_configurator.get_single_configuration(description)

            # The second element of gui_elements contains the element for user interaction, so this one is checked.
            user_element = gui_elements[1]

            # Check for a QCheckBox as potential element.
            if isinstance(user_element, QCheckBox):
                # Check for the correct configuration.
                assert user_element.isChecked() == configuration

            # Check for a QLineEdit as potential element.
            elif isinstance(user_element, QLineEdit):
                # Check for the correct configuration.
                assert configuration == user_element.text()

    def test_save_current_configuration_and_close(self):
        """
        Test the method for saving the current configuration and close after that.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        configuration_settings_dialog = ConfigurationSettingsDialog()
        # Ensure a visible dialog.
        assert configuration_settings_dialog.isVisible() is True
        # Save the configuration and close the dialog.
        configuration_settings_dialog.save_current_configuration_and_close()
        # The dialog should be invisible after a close.
        assert configuration_settings_dialog.isVisible() is False

    def test_check_for_unsaved_configurations(self):
        """
        Test the method for checking for unsaved configurations.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        configuration_settings_dialog = ConfigurationSettingsDialog()

        # At this moment, all configurations are saved/freshly initialized.
        assert configuration_settings_dialog.check_for_unsaved_configuration() is False

        # Change one existing element, so there are unsaved configurations.
        for gui_elements in configuration_settings_dialog.configuration_dictionary.values():
            # The second element is the element for user interaction.
            user_element = gui_elements[1]

            # Check for a checkbox.
            if isinstance(user_element, QCheckBox):
                # Get the current state of the checkbox.
                current_state = user_element.isChecked()
                # Reverse the state, so there is an unsaved configuration now.
                user_element.setChecked(not current_state)
                # Check for an unsaved configuration. This should be True.
                assert configuration_settings_dialog.check_for_unsaved_configuration() is True
                # Break the loop after an assertion.
                break

