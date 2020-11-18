import sys
import unittest

from PyQt5.QtCore import QBasicTimer
from PyQt5.QtWidgets import QApplication, QProgressBar, QLabel

from pygadmin.widgets.start_progress_dialog import StartProgressDialog
from pygadmin.connectionstore import global_connection_store


class TestStartProgressDialogMethods(unittest.TestCase):
    """
    Test the functionality and behavior of the start progress dialog.
    """

    def test_initial_attributes(self):
        """
        Test the initial attributes of the dialog.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a start progress dialog.
        start_progress_dialog = StartProgressDialog()

        # There should be a progress bar, because this is the whole idea of having a start progress dialog.
        assert isinstance(start_progress_dialog.progress_bar, QProgressBar)
        # There should also be a description label, informing about the current process.
        assert isinstance(start_progress_dialog.description_label, QLabel)
        # A timer is required for the functionality of the progress bar.
        assert isinstance(start_progress_dialog.timer, QBasicTimer)
        # The step at the beginning should be 0.
        assert start_progress_dialog.float_step == 0

    def test_progress_bar_with_zero_connections(self):
        """
        Test the functionality of the progress bar without connections in the connection store.
        """

        # Make a copy of the current connection list for storing it.
        connection_list = global_connection_store.get_connection_parameters_from_yaml_file()
        # Set the current list to an empty list.
        global_connection_store.connection_parameters_yaml = []
        # Delete all connections and store the empty list.
        global_connection_store.commit_current_list_to_yaml()

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a start progress dialog.
        start_progress_dialog = StartProgressDialog()

        # Start the progress bar without connections.
        start_progress_dialog.start_progress_bar()

        # Now the float step and the step size should be 100.
        assert start_progress_dialog.float_step == 100
        assert start_progress_dialog.step_size == 100

        # Restore the connection list.
        global_connection_store.connection_parameters_yaml = connection_list
        global_connection_store.commit_current_list_to_yaml()

    def test_progress_bar_with_connections(self):
        """
        Test the progress bar with existing connections.
        """

        # Define one dictionary for one connection.
        first_connection_dictionary = {"Host": "testhost",
                                       "Username": "testuser",
                                       "Database": "postgres",
                                       "Port": 5432}

        # Define another dictionary for a second connection.
        second_connection_dictionary = {"Host": "anothertesthost",
                                        "Username": "testuser",
                                        "Database": "postgres",
                                        "Port": 5432}

        # Load the current connections.
        global_connection_store.get_connection_parameters_from_yaml_file()
        # Insert the pre-defined dictionaries to the connection store, so there are at least two dictionaries.
        global_connection_store.save_connection_parameters_in_yaml_file(first_connection_dictionary)
        global_connection_store.save_connection_parameters_in_yaml_file(second_connection_dictionary)

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a start progress dialog.
        start_progress_dialog = StartProgressDialog()

        # Start the progress bar.
        start_progress_dialog.start_progress_bar()

        # Now the step should be start at 0.
        assert start_progress_dialog.float_step == 0
        # The step size should be smaller than 100, because there are at least two connection parameters in the global
        # connection store.
        assert start_progress_dialog.step_size < 100

        # Clean up, delete the two created connections.
        global_connection_store.delete_connection(first_connection_dictionary)
        global_connection_store.delete_connection(second_connection_dictionary)
