import sys
import unittest

from PyQt5.QtWidgets import QApplication, QLabel, QListWidget

from pygadmin.widgets.command_history import CommandHistoryDialog
from pygadmin.command_history_store import global_command_history_store
from pygadmin.configurator import global_app_configurator


class TestCommandHistoryDialogMethods(unittest.TestCase):
    """
    Test the functionality and methods of the command history dialog.
    """

    def test_empty_dialog(self):
        """
        Test the dialog without data in the command history store, so the dialog shows a warning about the empty
        history.
        """

        # Get the current command history for saving it during the testing of the method. Later, the current command
        # history is saved again in the command history store.
        current_command_history = global_command_history_store.get_command_history_from_yaml_file()

        # Delete all commands from the history, so the history is empty. As a result, the dialog should show the warning
        # ui.
        global_command_history_store.delete_all_commands_from_history()

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a command history dialog.
        command_history_dialog = CommandHistoryDialog()

        # Check for the existence and correct instance of the empty label.
        assert isinstance(command_history_dialog.empty_label, QLabel)

        # Set the list with the data about the last commands as command history list.
        global_command_history_store.command_history_list = current_command_history
        # Save the list in the yaml file again.
        global_command_history_store.commit_current_list_to_yaml()

    def test_initial_attributes(self):
        """
        Test the initial attributes of the dialog (with an existing command history).
        """

        # Define a dictionary with a command and the information about it, so there is at least one command in the
        # command history.
        command_dictionary = {"Command": "SELECT * FROM test;",
                              "Identifier": "testuser@testserver:5432/testdb",
                              "Time": "2020-10-01 11:53:59",
                              "Result": [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"],
                                         ["row D", "row E", "row F"]]}

        global_command_history_store.save_command_history_in_yaml_file(command_dictionary)

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a command history dialog.
        command_history_dialog = CommandHistoryDialog()

        # Check for the GUI attributes, so the QListWidget and the QLabels.
        assert isinstance(command_history_dialog.history_list_widget, QListWidget)
        assert isinstance(command_history_dialog.command_label, QLabel)
        assert isinstance(command_history_dialog.connection_identifier_label, QLabel)
        assert isinstance(command_history_dialog.date_time_label, QLabel)
        # The data list of the table model should be empty at the beginning.
        assert command_history_dialog.table_model.data_list == []

        # Check for the existence and correct instance of the command history list.
        assert isinstance(global_command_history_store.command_history_list, list)

        # Clean up, so the testing command is no longer part of the command history store.
        global_command_history_store.delete_command_from_history(command_dictionary)

    def test_show_command_information_in_labels(self):
        """
        Test the method for showing the command information in the given labels and the table view, so the data list of
        the table model is checked.
        """

        # Define a dictionary with a command and the information about it, so there is at least one command in the
        # command history.
        command_dictionary = {"Command": "SELECT * FROM test;",
                              "Identifier": "testuser@testserver:5432/testdb",
                              "Time": "2019-05-04 13:37:00",
                              "Result": [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"],
                                         ["row D", "row E", "row F"]]}

        global_command_history_store.save_command_history_in_yaml_file(command_dictionary)

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a command history dialog.
        command_history_dialog = CommandHistoryDialog()

        # Define an index for the last item for iterating. This index is used later for setting the current row as
        # selection.
        index_of_last_item = 0
        # Define an identifier text for finding the command of the previous defined command dictionary.
        command_identifier_text = "{}\n{}".format(command_dictionary["Command"], command_dictionary["Time"])

        # Iterate over every item in the list widget.
        for item_count in range(command_history_dialog.history_list_widget.count()):
            # If the text of the current item is the same as in the command identifier text, use the current item count
            # as index of the last item.
            if command_identifier_text == command_history_dialog.history_list_widget.item(item_count).text():
                index_of_last_item = item_count
                # End the loop, because further iterating is not necessary. There is already a match.
                break

        # Set the index of the last item as current row.
        command_history_dialog.history_list_widget.setCurrentRow(index_of_last_item)

        # Check the labels and the data list of the tree model for the correct list.
        assert command_history_dialog.command_label.text() == command_dictionary["Command"]
        assert command_history_dialog.connection_identifier_label.text() == command_dictionary["Identifier"]
        assert command_history_dialog.date_time_label.text() == command_dictionary["Time"]
        assert command_history_dialog.table_model.data_list == command_dictionary["Result"]

        # Clean up, so the testing command is no longer part of the command history store.
        global_command_history_store.delete_command_from_history(command_dictionary)

    def test_get_command_dictionary_of_current_selected_identifier(self):
        """
        Test the method for getting the command dictionary of the current selected identifier in the history list
        widget.
        """

        # Define a dictionary with a command and the information about it, so there is at least one command in the
        # command history.
        command_dictionary = {"Command": "SELECT * FROM test;",
                              "Identifier": "testuser@testserver:5432/testdb",
                              "Time": "2019-05-04 13:37:00",
                              "Result": [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"],
                                         ["row D", "row E", "row F"]]}

        global_command_history_store.save_command_history_in_yaml_file(command_dictionary)

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a command history dialog.
        command_history_dialog = CommandHistoryDialog()

        # Define an index for the last item for iterating. This index is used later for setting the current row as
        # selection.
        index_of_last_item = 0
        # Define an identifier text for finding the command of the previous defined command dictionary.
        command_identifier_text = "{}\n{}".format(command_dictionary["Command"], command_dictionary["Time"])

        # Iterate over every item in the list widget.
        for item_count in range(command_history_dialog.history_list_widget.count()):
            # If the text of the current item is the same as in the command identifier text, use the current item count
            # as index of the last item.
            if command_identifier_text == command_history_dialog.history_list_widget.item(item_count).text():
                index_of_last_item = item_count
                # End the loop, because further iterating is not necessary. There is already a match.
                break

        # Set the index of the last item as current row.
        command_history_dialog.history_list_widget.setCurrentRow(index_of_last_item)

        # Get the command dictionary of the selected command.
        selected_command_dictionary = command_history_dialog.get_command_dictionary_of_current_selected_identifier()

        # The dictionary of the selected item should be the command dictionary.
        assert selected_command_dictionary == command_dictionary

        # Clean up, so the testing command is no longer part of the command history store.
        global_command_history_store.delete_command_from_history(command_dictionary)

    def test_save_current_command_limit(self):
        """
        Test the function for saving the current command limit with the input in the line edit.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a command history dialog.
        command_history_dialog = CommandHistoryDialog()

        # Define a new command limit.
        new_command_limit = 15

        # Set the command limit as string as text of the command limit line edit.
        command_history_dialog.command_limit_line_edit.setText(str(new_command_limit))
        # Save the current command limit.
        command_history_dialog.save_current_command_limit()

        # The command limit in the app configurator should now be the pre-defined new command limit.
        assert global_app_configurator.get_single_configuration("command_limit") == new_command_limit

    def test_check_valid_command_limit(self):
        """
        Test the function for checking a valid comment limit in the command limit line edit.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a command history dialog.
        command_history_dialog = CommandHistoryDialog()

        # A normal text, which is not equivalent to None and cannot be casted to an integer, should be invalid.
        command_history_dialog.command_limit_line_edit.setText("test")
        assert command_history_dialog.check_valid_command_limit() is False

        # -1 as text can be casted to an integer, but the command limit needs to be larger than 0.
        command_history_dialog.command_limit_line_edit.setText("-1")
        assert command_history_dialog.check_valid_command_limit() is False

        # The text None should be accepted.
        command_history_dialog.command_limit_line_edit.setText("None")
        assert command_history_dialog.check_valid_command_limit() is True

        # The text 42 can be casted to a valid integer value.
        command_history_dialog.command_limit_line_edit.setText("42")
        assert command_history_dialog.check_valid_command_limit() is True


