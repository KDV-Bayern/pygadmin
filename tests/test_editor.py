import os
import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.widgets.editor import EditorWidget
from pygadmin.models.tablemodel import TableModel
from pygadmin.database_query_executor import DatabaseQueryExecutor
from pygadmin.connectionfactory import global_connection_factory


class TestEditorWidgetMethods(unittest.TestCase):
    """
    Test the functionality and methods of the editor widget.
    """

    def test_initial_attributes(self):
        """
        Check for the correct existence and instance of the initial attributes of the editor.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget.
        editor_widget = EditorWidget()

        # Test for the correct instance of the table model.
        assert isinstance(editor_widget.table_model, TableModel)
        # The data list of the table model should be empty at the start.
        assert editor_widget.table_model.data_list == []
        # The current database connection should be None at the start.
        assert editor_widget.current_database_connection is None
        # The connection identifier should be None at at the start.
        assert editor_widget.connection_identifier is None
        # Test for the correct instance of the database query executor.
        assert isinstance(editor_widget.database_query_executor, DatabaseQueryExecutor)
        
    def test_valid_set_connection_based_on_parameters(self):
        """
        Test the method for setting connection parameters based on parameters in a dictionary with valid connection
        parameters.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget.
        editor_widget = EditorWidget()

        # Define a connection parameter dictionary.
        connection_dictionary = {"host": "localhost",
                                 "database": "postgres",
                                 "port": 5432,
                                 "user": "testuser"}

        # Get a database connection related to the parameters in the connection dictionary.
        database_connection = global_connection_factory.get_database_connection(connection_dictionary["host"],
                                                                                connection_dictionary["user"],
                                                                                connection_dictionary["database"],
                                                                                connection_dictionary["port"])

        # Set the database connection of the editor based on the connection dictionary.
        editor_widget.set_connection_based_on_parameters(connection_dictionary)

        # After a successful set of a database connection, the data list of the table model should still be empty and
        # without an error message.
        assert editor_widget.table_model.data_list == []
        # The database connection of the editor should be the connection based on the connection dictionary.
        assert editor_widget.current_database_connection == database_connection

    def test_invalid_set_connection_based_on_parameters(self):
        """
        Test the method for setting connection parameters based on parameters in a dictionary with invalid connection
        parameters.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget.
        editor_widget = EditorWidget()

        # Define a connection parameter dictionary. The host parameter is an invalid parameter.
        connection_dictionary = {"host": "localhorst",
                                 "database": "postgres",
                                 "port": 5432,
                                 "user": "testuser"}

        # Try to set the connection with the function for setting a database connection.
        editor_widget.set_connection_based_on_parameters(connection_dictionary)

        # After a failed set of a database connection, there should be a warning in the table model.
        assert editor_widget.table_model.data_list != []
        # The current database connection should be None after this kind of failure.
        assert editor_widget.current_database_connection is None

    def test_refresh_table_model(self):
        """
        Test the method for refreshing the table model of the editor.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget.
        editor_widget = EditorWidget()

        # Define a list with new data.
        new_data_list = [["column 1, column 2"], (1, "row A", "row B"), (2, "row C", "row D")]
        # Use the function for refreshing the data list of the table model.
        editor_widget.refresh_table_model(new_data_list)
        # The data list of the table model should be the new data list.
        assert editor_widget.table_model.data_list == new_data_list

    def test_save_current_statement_in_file(self):
        """
        Test the function for saving the current statement in a file. User input is not necessary, because the file for
        saving is predefined.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget.
        editor_widget = EditorWidget()

        # Define a test text.
        test_text = "This is a text for testing."
        # Set the text as text of the query input editor for saving.
        editor_widget.query_input_editor.setText(test_text)

        # Define a test path.
        test_path = os.path.join(os.path.expanduser("~"), '.pygadmin_test')
        # Create the test path.
        os.mkdir(test_path)
        # Define a test file.
        test_file = os.path.join(test_path, "test_file.txt")

        # Use the test file as file for saving in the editor.
        editor_widget.corresponding_saved_file = test_file
        # Save the current statement and text of the query input editor in the pre defined test file.
        editor_widget.save_current_statement_in_file()

        # Open the test file.
        with open(test_file, "r") as test_file:
            # Get the text of the file, which should be the currently saved text.
            saved_editor_text = test_file.read()

        # Remove the file and the path as a clean up.
        os.remove(test_file.name)
        os.rmdir(test_path)

        # Check the text: The inserted text in the editor should be the text, which is saved in the file.
        assert test_text == saved_editor_text

    def test_is_editor_empty(self):
        """
        Test the method for an editor check: Is the editor empty or not?
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget.
        editor_widget = EditorWidget()

        # After creating the widget, it should be empty.
        assert editor_widget.is_editor_empty() is True

        # Set a text to the editor, so it is not empty anymore.
        editor_widget.query_input_editor.setText("Test Text")
        # The method should now return False.
        assert editor_widget.is_editor_empty() is False

        # Set also an title to the editor widget.
        editor_widget.setWindowTitle("Test Title")
        # The method should still return False, because the editor is not empty.
        assert editor_widget.is_editor_empty() is False

        # Set the text of the editor back to an empty string.
        editor_widget.query_input_editor.setText("")
        # Set the text to a string with content.
        editor_widget.setWindowTitle("Test Title")
        # The editor widget should not be empty.
        assert editor_widget.is_editor_empty() is False

    def test_get_connection_status_string_for_window_title(self):
        """
        Test the method for determining the connection part of the window title based on the different kinds of
        connections and their validity.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget.
        editor_widget = EditorWidget()

        # After the creation of the editor widget, the connection status string should be an empty string.
        assert editor_widget.get_connection_status_string_for_window_title() == ""

        # Set the database connection of the editor to False for simulating a failed database connection.
        editor_widget.current_database_connection = False
        # Now there should be an alert to a failed connection.
        assert editor_widget.get_connection_status_string_for_window_title() == "Connection failed: None"

        # Simulate a valid database connection with setting it to True.
        editor_widget.current_database_connection = True
        # Define an identifier for the connection simulation.
        test_identifier = "Test identifier"
        # Set the test identifier as connection identifier of the editor.
        editor_widget.connection_identifier = test_identifier
        # The connection string for the window title should be the connection identifier for a valid database
        # connection.
        assert editor_widget.get_connection_status_string_for_window_title() == test_identifier

    def test_get_corresponding_file_name_string_for_window_title_and_description(self):
        """
        Test the method for getting the name of the file save path for the editor to set the correct window title.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget.
        editor_widget = EditorWidget()

        # After the creation and without a corresponding saved file, the method should return a tuple of empty strings.
        assert editor_widget.get_corresponding_file_name_string_for_window_title_and_description() == ("", "")

        # Define a path for the test save file.
        save_file_path = "test/testfile/"
        # Define a name for the test save file.
        save_file_name = "test.sql"
        # Create a full path with path and name together.
        full_save_file_path = "{}{}".format(save_file_path, save_file_name)
        # Set the full path as corresponding saved file for simulating the behavior of a QFileDialog.
        editor_widget.corresponding_saved_file = full_save_file_path

        # Now the output should be the name of the file and the full path.
        assert editor_widget.get_corresponding_file_name_string_for_window_title_and_description() == (
            save_file_name, full_save_file_path)

    def test_get_file_save_status_string_for_window_title(self):
        """
        Test the method for checking the current status of the text in the query input editor of the editor compared to
        its last saved version.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget.
        editor_widget = EditorWidget()

        # The text in the editor should empty, so there should not be a change. The file save string should be empty.
        assert editor_widget.get_file_save_status_string_for_window_title() == ""

        # Set a text to the editor, so the initial text has changed.
        editor_widget.query_input_editor.setText("Test text")
        # After the text change, there should be the information about it in the file save string.
        assert editor_widget.get_file_save_status_string_for_window_title() == " (*)"

    def test_get_query_in_input_editor(self):
        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create an editor widget.
        editor_widget = EditorWidget()

        # Define a start text for testing, so this text can be chosen for a plain and simple selection later.
        test_text_start = "Test"
        # Define an end text for testing.
        test_text_end = " Text"
        # Put the two strings together as test text.
        test_text = "{}{}".format(test_text_start, test_text_end)
        # Set the test text as text of the query input editor.
        editor_widget.query_input_editor.setText(test_text)

        # The query in the query input editor should be the test text.
        assert editor_widget.get_query_in_input_editor() == test_text

        # Set the selection to the test text start.
        editor_widget.query_input_editor.setSelection(0, 0, 0, len(test_text_start))
        # Now the function for getting the query should return the test text start.
        assert editor_widget.get_query_in_input_editor() == test_text_start

