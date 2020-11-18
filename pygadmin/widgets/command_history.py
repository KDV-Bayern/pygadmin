import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QDialog, QLabel, QListWidget, QGridLayout, QPushButton, QLineEdit, QMessageBox

from pygadmin.command_history_store import global_command_history_store
from pygadmin.configurator import global_app_configurator
from pygadmin.widgets.widget_icon_adder import IconAdder


class CommandHistoryDialog(QDialog):
    """
    Create a dialog for showing the previous executed commands in the editor, which are saved in a history.
    """

    # Define a signal for getting the current selected command after a double click.
    get_double_click_command = pyqtSignal(str)

    def __init__(self):
        """
        Initialize the dialog based on the previous commands: If the command list is empty, this dialog does not need to
        show the command selection UI.
        """

        super().__init__()
        self.setModal(True)

        # Add the pygadmin icon as window icon.
        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)

        # Get the current command history list.
        command_history_list = global_command_history_store.get_command_history_from_yaml_file()

        # Check the command history list for emptiness. If the list is empty, shown a UI with an information about the
        # empty list.
        if not command_history_list:
            self.show_empty_ui()

        # In this case, the list is not empty and the previous commands can be shown properly.
        else:
            # Get the reversed list, so the newest command is at the top of the list.
            command_history_list.reverse()
            self.command_history_list = command_history_list
            self.init_ui()
            self.init_grid()

    def show_empty_ui(self):
        """
        Show an empty user interface with only one label for the information about an empty history.
        """

        # Create a label for informing about the empty history.
        self.empty_label = QLabel("There are currently no commands in your history.")
        # Place the label in a grid layout.
        grid_layout = QGridLayout(self)
        grid_layout.addWidget(self.empty_label, 0, 0)
        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

        # Set a maximum size and show the widget.
        self.setMaximumSize(200, 60)
        self.setWindowTitle("Command History Information")
        self.show()

    def init_ui(self):
        """
        Initialize the main user interface.
        """

        # Create a list widget for showing the main information about a previous SQL command.
        self.history_list_widget = QListWidget()
        # Define labels for showing the information about a previous command.
        self.command_label = QLabel("SQL Command")
        # Set the command text as selectable.
        self.command_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # Define a label for the date and the time.
        self.date_time_label = QLabel("Date and Time")
        # Define a label for the connection identifier.
        self.connection_identifier_label = QLabel("Connection Identifier")

        # Add a line edit for changing the command limit.
        self.command_limit_line_edit = QLineEdit()
        # Load the current limit in the line edit.
        self.load_current_command_limit_in_line_edit()

        # Create a button for saving a command limit.
        self.save_command_limit_button = QPushButton("Save Command Limit")
        # Connect the button with the function for checking and saving the command limit with user interaction.
        self.save_command_limit_button.clicked.connect(self.check_and_save_command_limit)

        # Create a button for deleting the current selected command.
        self.delete_selected_command_button = QPushButton("Delete Selected Command")
        # Set the button to disabled, because at the beginning, there is no selected item.
        self.delete_selected_command_button.setEnabled(False)
        # Connect the button with the function for deleting the selected command.
        self.delete_selected_command_button.clicked.connect(self.delete_selected_command)

        # Create a button for deleting the full history.
        self.delete_full_history_button = QPushButton("Delete Full History")
        # Connect the button with the function for deleting the history after asking the user, if they really want to
        # delete the full history.
        self.delete_full_history_button.clicked.connect(self.delete_full_command_history_after_user_question)

        # Initialize the command history.
        self.init_command_history()

        # Connect the signal for changing the selection in the list widget with the method for showing the information
        # about a previous command in the pre-defined QLabels.
        self.history_list_widget.itemSelectionChanged.connect(self.show_command_information_in_labels)

        self.history_list_widget.doubleClicked.connect(self.use_current_command_in_editor)

        self.setMaximumSize(1280, 720)
        self.setWindowTitle("Command History Information")
        self.show()

    def init_grid(self):
        """
        Initialize a grid layout as layout of the dialog.
        """

        grid_layout = QGridLayout(self)

        # Set the list widget as one big widget on the left of the application.
        grid_layout.addWidget(self.history_list_widget, 0, 0, 5, 1)
        # Place the information labels on the right.
        grid_layout.addWidget(self.command_label, 0, 1)
        grid_layout.addWidget(self.date_time_label, 1, 1)
        grid_layout.addWidget(self.connection_identifier_label, 2, 1)
        # Add the line edit and the buttons for saving and deleting under the list widget and the components with
        # information about the command.
        grid_layout.addWidget(self.command_limit_line_edit, 6, 0)
        grid_layout.addWidget(self.save_command_limit_button, 6, 1)
        grid_layout.addWidget(self.delete_selected_command_button, 7, 1)
        grid_layout.addWidget(self.delete_full_history_button, 8, 1)

        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def init_command_history(self):
        """
        Initialize the command history in the list widget for the history. Add every previous command to the
        """

        # Define a counter for inserting items to the history list widget.
        command_history_number_count = 0

        # Add every previous command to the list widget.
        for command_dictionary in self.command_history_list:
            # Create a unique command identifier, based on the command itself and the used time.
            command_identifier = "{}\n{}".format(command_dictionary["Command"], command_dictionary["Time"])
            # Insert the identifier with the counter as a place in the list widget.
            self.history_list_widget.insertItem(command_history_number_count, command_identifier)
            # Increment the number count for the next item.
            command_history_number_count += 1

    def get_command_dictionary_of_current_selected_identifier(self):
        """
        Get the command dictionary for the current selected command identifier.
        """

        # Check for selected items.
        if self.history_list_widget.selectedItems():
            # Get the text of the selected item.
            selected_item_text = self.history_list_widget.selectedItems()[0].text()

            # Use the command history list for finding the match.
            for command_dictionary in self.command_history_list:
                # Define a command identifier for finding the correct dictionary for showing the information.
                command_identifier = "{}\n{}".format(command_dictionary["Command"], command_dictionary["Time"])

                # Check for a match.
                if command_identifier == selected_item_text:
                    # Return the command dictionary with a match.
                    return command_dictionary

    def show_command_information_in_labels(self):
        """
        Show the information about a selected command in the QLabels.
        """

        command_dictionary = self.get_command_dictionary_of_current_selected_identifier()

        if command_dictionary is not None:
            # Change the text of the labels and the data of the table to the items of the dictionary.
            self.command_label.setText(command_dictionary["Command"])
            self.date_time_label.setText(command_dictionary["Time"])
            self.connection_identifier_label.setText(command_dictionary["Identifier"])

            # Enable the button for deleting the selected command.
            self.delete_selected_command_button.setEnabled(True)

    def load_current_command_limit_in_line_edit(self):
        """
        Load the current command limit out of the app configurator into the line edit.
        """

        # Get the current command limit out of the configurator.
        command_limit = global_app_configurator.get_single_configuration("command_limit")
        # Set the current command limit as text in the command limit line edit. The cast to string is used for the
        # command limit "None".
        self.command_limit_line_edit.setText(str(command_limit))

    def save_current_command_limit(self):
        """
        Save the current command limit of the line edit in the global app configurator.
        """

        # Get the current text of the command line edit.
        command_limit_line_edit_text = self.command_limit_line_edit.text()

        # If the text is None, then the new command limit is None.
        if command_limit_line_edit_text == "None":
            new_command_limit = None

        # If the text is not None, it is a valid string, which can be casted to an integer value.
        else:
            new_command_limit = int(command_limit_line_edit_text)

        # Save the new command limit.
        global_app_configurator.set_single_configuration("command_limit", new_command_limit)
        # Save the configuration data in a persistent yaml file.
        global_app_configurator.save_configuration_data()

    def check_valid_command_limit(self):
        """
        Check for a valid command limit in the line edit.
        """

        # Get the current user input for the command limit out of the command limit line edit.
        command_limit = self.command_limit_line_edit.text()

        # If the input for the command limit is None as text, return True, because None is a valid text for showing a
        # non-existing limit.
        if command_limit == "None":
            return True

        # Try to cast the command limit to an integer. This works in case of a valid string with a possible cast.
        try:
            # Get the command limit as integer.
            command_limit = int(command_limit)

            # The command limit is valid, if it is larger than 0, so True is returned in this case. As a consequence,
            # False is returned in the invalid cases.
            return command_limit > 0

        # Return False for a value error, because in this case, the command limit is invalid.
        except ValueError:
            return False

    def check_and_save_command_limit(self):
        """
        Check for a valid command limit in the command limit line edit. If the limit is invalid, show a message to the
        user about the invalidity. If the limit is valid, save the limit, inform the command history store and the user
        about the success.
        """

        if self.check_valid_command_limit() is False:
            QMessageBox.critical(self, "Command Limit Error", "The command limit you entered is invalid. Please enter"
                                                              "an integer number larger than 0 or None, if you do "
                                                              "not wish to use a limit.")

            return

        # Save the current command limit in the global app configurator.
        self.save_current_command_limit()
        # Inform the global command history store about a new limit and adjust the saved history to the new command
        # limit.
        global_command_history_store.adjust_saved_history_to_new_command_limit()
        # Save the current list in the yaml file.
        global_command_history_store.commit_current_list_to_yaml()

        QMessageBox.information(self, "Command Limit Saved", "The new command limit was saved successfully. Potential "
                                                             "changes in the command history dialog may apply after "
                                                             "a reopening of the dialog.")

    def delete_selected_command(self):
        """
        Get the command dictionary of the current selected command identifier and delete it in the list widget and in
        the global command history.
        """

        # Get the command dictionary of the current selected identifier.
        command_dictionary = self.get_command_dictionary_of_current_selected_identifier()
        # Delete the selected item in the list widget with the method takeItem. The current row is the current selected
        # item. An additional or manual deletion process is not necessary, because this is the world of Python with a
        # functional garbage collection.
        self.history_list_widget.takeItem(self.history_list_widget.currentRow())
        # Delete the command in the history.
        global_command_history_store.delete_command_from_history(command_dictionary)
        # Clear the selection in the list widget.
        self.history_list_widget.selectionModel().clear()
        # Deactivate the button for deleting the selected command, because there is no selected command.
        self.delete_selected_command_button.setEnabled(False)

    def delete_full_command_history(self):
        """
        Delete the full command history and close the dialog after the deletion.
        """

        global_command_history_store.delete_all_commands_from_history()
        self.close()

    def delete_full_command_history_after_user_question(self):
        """
        Delete the full command history after a confirmation by the user.
        """

        delete_full_command_history = QMessageBox.question(self, "Delete Full Command History", "Do you really want to"
                                                                                                "delete the full "
                                                                                                "command history?",
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if delete_full_command_history == QMessageBox.Yes:
            self.delete_full_command_history()

    def use_current_command_in_editor(self):
        """
        Get the current selected command after a double click. Emit a signal, so the command can be used be the editor
        in the main window.
        """

        # Get the dictionary of the selected command.
        selected_command_dictionary = self.get_command_dictionary_of_current_selected_identifier()

        # Try to get the selected command in the dictionary with its key.
        try:
            selected_command = selected_command_dictionary["Command"]
            # Emit the signal with the selected command.
            self.get_double_click_command.emit(selected_command)
            # Close the dialog, because browsing the history is no longer necessary.
            self.close()

        except KeyError:
            logging.critical("The selected dictionary for commands in the command history does not contain the key"
                             "command: {}".format(selected_command_dictionary))

