from PyQt5.QtWidgets import QDialog, QLabel, QGridLayout, QCheckBox, QPushButton, QMessageBox, QLineEdit, QFileDialog

from pygadmin.configurator import global_app_configurator
from pygadmin.widgets.widget_icon_adder import IconAdder


class ConfigurationSettingsDialog(QDialog):
    """
    Use a dialog for configure the setting in app_configuration.yaml with a GUI and the help of the global app
    configurator.
    """

    def __init__(self):
        """
        Make sub functions for initializing the widget, separated by the parts user interface and grid layout.
        """

        super().__init__()
        self.setModal(True)
        # Add the pygadmin icon as window icon.
        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)
        self.init_ui()
        self.init_grid()

    def init_ui(self):
        """
        Design the user interface and its components.
        """

        # Ensure that all current data in the following dictionary has been loaded.
        global_app_configurator.load_configuration_data()
        # Get all current configurations in a dictionary.
        configurations_dictionary = global_app_configurator.get_all_current_configurations()
        # Define a class dictionary for the configuration details with its GUI components.
        self.configuration_dictionary = {}

        # Define a label with the purpose of the widget as description.
        self.settings_description_label = QLabel("Edit the current configuration settings of pygadmin")

        # Predefined a path for the pg_dump executable.
        pg_dump_path = None

        # Check all descriptions and values of a configuration in the dictionary with the configurations.
        for configuration_description, current_configuration_value in configurations_dictionary.items():
            # Make the configuration description more readable for the user.
            configuration_description = configuration_description.replace("_", " ")
            if isinstance(current_configuration_value, bool):
                # Create a label with a description for every configuration.
                configuration_description_label = QLabel(configuration_description)
                # Create a checkbox for every configuration.
                configuration_checkbox = QCheckBox("Active")

                # If the current configuration is True, the configuration is active.
                if current_configuration_value is True:
                    # Set the checkbox for an active configuration as checked.
                    configuration_checkbox.setChecked(True)

                # Save all the created components in the dictionary.
                self.configuration_dictionary[configuration_description] = [configuration_description_label,
                                                                            configuration_checkbox]
            # Check the description for a pg dump path.
            if configuration_description == "pg_dump_path":
                # If a path exists, use the pre defined variable.
                pg_dump_path = current_configuration_value

        # Create a label for the path.
        self.pg_dump_path_label = QLabel("pg_dump path")
        # Create a line edit for the path. The path can be edited manually.
        self.pg_dump_line_edit = QLineEdit()
        # Save the current information about the description and the GUI elements in a dictionary.
        self.configuration_dictionary["pg_dump_path"] = [self.pg_dump_path_label, self.pg_dump_line_edit]

        # Check the pg_dump path. If there was a previous path, set the path as text in the line edit.
        if pg_dump_path is not None:
            self.pg_dump_line_edit.setText(pg_dump_path)

        # Create a button for choosing a file.
        self.pg_dump_button = QPushButton("...")
        # Connect the button with the function for choosing a path/file for the pg_dump executable.
        self.pg_dump_button.clicked.connect(self.choose_pg_dump_path)

        # Create a button for saving the current configuration and closing after saving.
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_current_configuration_and_close)
        # Create a button for applying the changes without closing.
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.save_current_configuration)
        # Create a button for canceling the input.
        self.cancel_button = QPushButton("Cancel")
        # Set a maximum size for the cancel button, so the button is not too prominent.
        self.cancel_button.setMaximumSize(90, 30)
        self.cancel_button.clicked.connect(self.close_with_check_for_unsaved_configuration)

        self.setWindowTitle("Settings")
        # Define a maximum size for the widget and show the widget with the maximum size.
        self.setMaximumSize(720, 160)
        self.showMaximized()
        self.show()

    def init_grid(self):
        """
        Set a grid layout to the widget and place all its components.
        """

        # Define the layout.
        grid_layout = QGridLayout(self)

        # Add the description label.
        grid_layout.addWidget(self.settings_description_label, 0, 0)

        # Create an incrementer for placing the components in the dictionary at the right place.
        grid_incrementer = 1

        # Iterate over all values of the dictionary with all configurations.
        for configuration_gui_elements in self.configuration_dictionary.values():
            # Place the description on the left.
            grid_layout.addWidget(configuration_gui_elements[0], grid_incrementer, 0)
            # Place the checkbox on the right.
            grid_layout.addWidget(configuration_gui_elements[1], grid_incrementer, 2, 1, 2)
            grid_incrementer += 1

        # Place the components for the pg dump information.
        grid_layout.addWidget(self.pg_dump_path_label, grid_incrementer, 0)
        grid_layout.addWidget(self.pg_dump_line_edit, grid_incrementer, 1)
        grid_layout.addWidget(self.pg_dump_button, grid_incrementer, 2)
        grid_incrementer += 1

        # Place the buttons below the description and the checkbox.
        grid_layout.addWidget(self.cancel_button, grid_incrementer, 0)
        grid_layout.addWidget(self.save_button, grid_incrementer, 1)
        grid_layout.addWidget(self.apply_button, grid_incrementer, 2)

        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def save_current_configuration(self):
        """
        Save the current configuration data based on the status of the checkboxes.
        """

        # Check every configuration and every checkbox.
        for configuration_description, configuration_elements in self.configuration_dictionary.items():
            # Replace the more readable " " with the "_" for saving.
            configuration_description = configuration_description.replace(" ", "_")
            user_element = configuration_elements[1]

            # Check for a check box as GUI element.
            if isinstance(user_element, QCheckBox):
                # Set the configuration based on the description and the current status of the checkbox. If the box is
                # checked, submit a True, if not, a False.
                global_app_configurator.set_single_configuration(configuration_description, user_element.isChecked())

            # Check for a line edit as GUI element.
            elif isinstance(user_element, QLineEdit):
                global_app_configurator.set_single_configuration(configuration_description, user_element.text())

        # Save the current configuration data in the file.
        global_app_configurator.save_configuration_data()

        # Return True for a success.
        return True

    def save_current_configuration_and_close(self):
        """
        Use the function for saving the current configuration data and close the dialog after saving.
        """

        # Save the current configuration with the designated function.
        self.save_current_configuration()
        # Close the dialog.
        self.close()

    def check_for_unsaved_configuration(self):
        """
        Check for a potential unsaved configuration configuration by the saved configuration of the global app
        configurator and the status of the checkboxes. If there is a match as unsaved connection, return True.
        """

        # Ensure the load of all current data for the following method call.
        global_app_configurator.load_configuration_data()
        # Get the previous configuration.
        previous_configuration = global_app_configurator.get_all_current_configurations()

        # Check every element in the previous configuration.
        for configuration_key, configuration_value in previous_configuration.items():
            # Use the more readable version.
            configuration_key = configuration_key.replace("_", " ")
            # Check every in the class dictionary for the configurations with the description and the GUI elements.
            for configuration_description, configuration_elements in self.configuration_dictionary.items():
                # Define the second element of the list of configuration as user element - because it is used for user
                # input.
                user_element = configuration_elements[1]
                # Check for a checkbox as GUI element.
                if isinstance(user_element, QCheckBox):
                    # If the two configurations keys/descriptions are identical, check for the configuration value.
                    # Check for the boolean of the previous configuration. Check also for the status of the checkbox. If
                    # the booleans are identical, nothing has changed. If they are not, there is an unsaved
                    # configuration.
                    if configuration_key == configuration_description \
                            and configuration_value != user_element.isChecked():
                        # Return True for an unsaved configuration.
                        return True

                # Check for a QLineEdit as GUI element.
                elif isinstance(user_element, QLineEdit):
                    # If the configuration key matches with the description and the value is different to the previous
                    # one, proceed.
                    if configuration_key == configuration_description \
                            and configuration_value != user_element.text():
                        # Return True for an unsaved configuration.
                        return True

        # If this point is reached, there is no match and as a result, there are not any unsaved configurations.
        return False

    def close_with_check_for_unsaved_configuration(self):
        """
        Close the current dialog with a check for unsaved configurations. If there is an unsaved configuration, ask the
        user for the following procedure.
        """

        # Check for an unsaved configuration.
        if self.check_for_unsaved_configuration():
            # If there is an unsaved configuration, ask the user.
            proceed_with_unsaved_changes = QMessageBox.question(self, "Proceed with unsaved changes?",
                                                                "Do you want to close the dialog with unsaved changes? "
                                                                "These changes will be deleted without saving.")

            # Check for the user's answer.
            if proceed_with_unsaved_changes == QMessageBox.No:
                # If the user does not want to proceed and delete unsaved changes, end the function with a return.
                return

        # Close the dialog for all cases without unsaved changes or with user consent.
        self.close()

    def choose_pg_dump_path(self):
        """
        Choose a path for the pg_dump executable and use it as text in the related QLineEdit.
        """

        # Get a file name and type with a QFileDialog.
        choose_dialog_file_and_type = QFileDialog.getOpenFileName(self, "Use pg_dump executable")
        # The file name is the first part of the resulting tuple.
        file_name = choose_dialog_file_and_type[0]

        # If the file name is not an empty string, proceed.
        if file_name != "":
            # Set the file name with its path as text of the QLineEdit.
            self.pg_dump_line_edit.setText(file_name)
