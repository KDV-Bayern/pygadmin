import sys
import unittest
import keyring

from PyQt5.QtWidgets import QApplication, QLineEdit, QListWidgetItem

from pygadmin.widgets.connection_dialog import ConnectionDialogWidget
from pygadmin.connectionstore import global_connection_store


class TestConnectionDialogMethods(unittest.TestCase):
    """
    Test the functionality and methods of the connection dialog in some essential aspects.
    """

    def test_initial_attributes(self):
        """
        Test basic attributes of the class after initializing.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Check for the connection parameter edit dictionary, which is an essential element to the dialog.
        assert isinstance(connection_dialog.connection_parameter_edit_dictionary, dict)

        # Check every value in the dictionary for a QLineEdit.
        for value in connection_dialog.connection_parameter_edit_dictionary.values():
            # The elements should be QLineEdits.
            assert isinstance(value, QLineEdit)

        # The label for the status for testing the given connection should have the correct text.
        assert connection_dialog.test_given_connection_status_label.text() == "Not tested yet"

    def test_check_for_empty_parameter_fields(self):
        """
        Test the function for checking for empty parameter fields.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Get the current result for the check of empty parameter fields. It should not be a simple boolean, so it will
        # be a list.
        empty_parameter_result = connection_dialog.check_for_empty_parameter_edit_fields()

        # The first parameter of the result list is a boolean, which should be True in this case.
        assert empty_parameter_result[0] is True

        # Set to every edit field a value.
        for edit_field in connection_dialog.connection_parameter_edit_dictionary.values():
            edit_field.setText("42")

        # After setting values to every edit field, there should not be an empty parameter edit field.
        assert connection_dialog.check_for_empty_parameter_edit_fields() is False

    def test_check_for_valid_port(self):
        """
        Test the function for checking for a valid port in the port line edit.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Get the port line edit.
        port_line_edit = connection_dialog.connection_parameter_edit_dictionary["Port"]

        # Set a string, which can not be casted to an int, as text for the port.
        port_line_edit.setText("This is a triumph. I'm making a note here, huge success.")
        # The check for a valid port should be False.
        assert connection_dialog.check_for_valid_port() is False

        # Set a string, which can be casted to an int, as text for the port. The int in this case is invalid.
        port_line_edit.setText("-42")
        # The check for a valid port should still be False.
        assert connection_dialog.check_for_valid_port() is False

        # Set a valid and an int, which can be casted to int, as port.
        port_line_edit.setText("42")
        # The check for a valid port should now be True.
        assert connection_dialog.check_for_valid_port() is True

    def test_check_for_changed_password(self):
        """
        Test the method for checking for a changed password in the QLineEdit for the password compared to the password
        in the password manager.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Define the name of the service.
        service = "Pygadmin"
        # Define the identifier for the password
        password_identifier = "testuser@random:5432"
        # Choose a password.
        password = "unsafe"
        # Set the password in the keyring.
        keyring.set_password(service, password_identifier, password)

        # Get the line edit for the password.
        password_line_edit = connection_dialog.connection_parameter_edit_dictionary["Password"]
        # Set the currently saved password as text.
        password_line_edit.setText(password)
        # The function for checking for a changed password should now be False.
        assert connection_dialog.check_for_changed_password(password_identifier) is False

        # Change the text in the password line edit to another password.
        password_line_edit.setText("unsafe again")
        # Now there should be a changed password compared to the password manager, so the result should be True.
        assert connection_dialog.check_for_changed_password(password_identifier) is True

        # Clean up, so the password identifier and the password for testing are not a part of the password manager.
        keyring.delete_password(service, password_identifier)

    def test_set_password_with_identifier(self):
        """
        Test the method for setting a password with its identifier.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Define the identifier for the password
        password_identifier = "testuser@random:5432"

        # Get the password line edit.
        password_line_edit = connection_dialog.connection_parameter_edit_dictionary["Password"]
        # Set a text as password in the password line edit.
        password_line_edit.setText("unsafe")
        # The function for setting the password with its identifier should be True.
        assert connection_dialog.set_password_with_its_identifier(password_identifier) is True

        # Clean up, so the password identifier and the password for testing are not a part of the password manager.
        keyring.delete_password("Pygadmin", password_identifier)

    def test_valid_find_occurrence_in_list_widget_and_select_item(self):
        """
        Test the method for finding the occurrence of an item in a list widget. The item should be selected after the
        call of the method. Use valid connection parameters, which are also part of the connection store.
        """

        # Define a connection dictionary for saving the connection data in the connection store and creating a
        # connection identifier later, so the connection is part of the list widget and can be selected.
        connection_dictionary = {"Host": "random",
                                 "Username": "testuser",
                                 "Port": 5432,
                                 "Database": "postgres"}

        # Save the connection in the connection store.
        global_connection_store.save_connection_parameters_in_yaml_file(connection_dictionary)
        # Save the current connections in the connection store in the yaml file.
        global_connection_store.commit_current_list_to_yaml()

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Define a connection identifier for selecting it in the list widget.
        connection_identifier = "{}@{}:{}/{}".format(connection_dictionary["Username"], connection_dictionary["Host"],
                                                     connection_dictionary["Port"], connection_dictionary["Database"])

        # Get the item related to the connection identifier.
        item = connection_dialog.find_occurrence_in_list_widget_and_select_item(connection_identifier)

        # The item should be a QListWidgetItem.
        assert isinstance(item, QListWidgetItem)
        # The text of the item should be the connection identifier.
        assert item.text() == connection_identifier

        # Get the list of selected items.
        selected_items = connection_dialog.connection_parameters_list_widget.selectedItems()
        # Only one item should be selected, so the list should contain only one element.
        assert len(selected_items) == 1

        # Get the selected item.
        selected_item = selected_items[0]
        # The selected item should be the item, which is returned by the function.
        assert selected_item == item

        # Clean up, so the test connection is no longer part of the connection store.
        global_connection_store.delete_connection(connection_dictionary)
        global_connection_store.commit_current_list_to_yaml()

    def test_invalid_find_occurrence_in_list_widget_and_select_item(self):
        """
        Test the method for finding the occurrence of an item in a list widget. Use invalid connection parameters for
        testing the error case, so the connection identifier is not based on existing connection parameters in the
        connection store.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Get a non existing item in the list widget.
        item = connection_dialog.find_occurrence_in_list_widget_and_select_item(None)
        # The item should be None.
        assert item is None

        # Check for the selected items in the list widget.
        selected_items = connection_dialog.connection_parameters_list_widget.selectedItems()
        # The list of selected items should be empty.
        assert selected_items == []

    def test_get_all_item_texts_in_list_widget(self):
        """
        Test the method for getting all the texts of the items/connection identifiers in the list widget.
        """

        # Create a list for storing all connection identifiers.
        connection_identifiers = []

        # Use every dictionary of a connection in the connection store to create an identifier for the connection.
        for connection_dictionary in global_connection_store.connection_parameters_yaml:
            # Create the connection identifier.
            identifier = "{}@{}:{}/{}".format(connection_dictionary["Username"], connection_dictionary["Host"],
                                              connection_dictionary["Port"], connection_dictionary["Database"])

            # Append the identifier to the list of connection identifiers.
            connection_identifiers.append(identifier)

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()
        # Get all item texts.
        item_texts = connection_dialog.get_all_item_texts_in_list_widget()

        # Iterate over every identifier for checking its existence in the item texts.
        for identifier in connection_identifiers:
            # The identifier should be part of the item texts.
            assert identifier in item_texts

    def test_method_for_testing_database_connection(self):
        """
        Test the method for testing for a valid database connection based on the current text in the QLineEdits.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # The text of the connection status label should be "Not tested yet", because a connection is not tested.
        assert connection_dialog.test_given_connection_status_label.text() == "Not tested yet"

        # Set valid connection parameters for testing a connection.
        connection_dialog.connection_parameter_edit_dictionary["Host"].setText("localhost")
        connection_dialog.connection_parameter_edit_dictionary["Username"].setText("testuser")
        connection_dialog.connection_parameter_edit_dictionary["Database"].setText("postgres")
        connection_dialog.connection_parameter_edit_dictionary["Port"].setText("5432")
        # Test the connection with the method.
        connection_dialog.test_current_database_connection()
        # The label should now show a valid database connection, because valid parameters are used.
        assert connection_dialog.test_given_connection_status_label.text() == "Connection Valid"

        # Set a new text as host, so after a new test, the connection is invalid.
        connection_dialog.connection_parameter_edit_dictionary["Host"].setText("localhorst")
        # After changing the text, the label should switch back to "Not tested yet"
        assert connection_dialog.test_given_connection_status_label.text() == "Not tested yet"

        # Test the database connection now.
        connection_dialog.test_current_database_connection()
        # The label should now show an invalid connection.
        assert connection_dialog.test_given_connection_status_label.text() == "Connection Invalid"

    def test_insert_parameters_in_edit_fields(self):
        """
        Test the method for inserting parameters in the QLineEdit fields based on the signal for a change in the
        selection of the list widget.
        """

        # Define a connection dictionary for saving the connection data in the connection store and creating a
        # connection identifier later, so the connection is part of the list widget and can be selected.
        connection_dictionary = {"Host": "random",
                                 "Username": "testuser",
                                 "Port": 5432,
                                 "Database": "postgres"}

        # Save the connection in the connection store.
        global_connection_store.save_connection_parameters_in_yaml_file(connection_dictionary)
        # Save the current connections in the connection store in the yaml file.
        global_connection_store.commit_current_list_to_yaml()

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Define a connection identifier for selecting it in the list widget.
        connection_identifier = "{}@{}:{}/{}".format(connection_dictionary["Username"], connection_dictionary["Host"],
                                                     connection_dictionary["Port"], connection_dictionary["Database"])

        # Select the item based on the connection identifier in the list widget.
        connection_dialog.find_occurrence_in_list_widget_and_select_item(connection_identifier)

        # Check the correct content of the QLineEdit fields. They should contain the parameters of the connection
        # dictionary.
        assert connection_dictionary["Host"] == connection_dialog.connection_parameter_edit_dictionary["Host"].text()
        assert connection_dictionary["Username"] \
               == connection_dialog.connection_parameter_edit_dictionary["Username"].text()
        # Cast the port to string, because it is saved in the dictionary as integer.
        assert str(connection_dictionary["Port"]) \
               == connection_dialog.connection_parameter_edit_dictionary["Port"].text()
        assert connection_dictionary["Database"] \
               == connection_dialog.connection_parameter_edit_dictionary["Database"].text()

        # Clean up, so the test connection is no longer part of the connection store.
        global_connection_store.delete_connection(connection_dictionary)
        global_connection_store.commit_current_list_to_yaml()

    def test_get_selected_connection(self):
        """
        Test the function for getting the selected connection, which returns a boolean and sets a result as an
        attribute.
        """

        # Define a connection dictionary for saving the connection data in the connection store and creating a
        # connection identifier later, so the connection is part of the list widget and can be selected.
        connection_dictionary = {"Host": "random",
                                 "Username": "testuser",
                                 "Port": 5432,
                                 "Database": "postgres"}

        # Save the connection in the connection store.
        global_connection_store.save_connection_parameters_in_yaml_file(connection_dictionary)
        # Save the current connections in the connection store in the yaml file.
        global_connection_store.commit_current_list_to_yaml()

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # A selected connection is missing, so the method should return False.
        assert connection_dialog.get_selected_connection() is False

        # Define a connection identifier for selecting it in the list widget.
        connection_identifier = "{}@{}:{}/{}".format(connection_dictionary["Username"], connection_dictionary["Host"],
                                                     connection_dictionary["Port"], connection_dictionary["Database"])

        # Select the item related to the connection identifier.
        connection_dialog.find_occurrence_in_list_widget_and_select_item(connection_identifier)

        # Now the method should return True, because an identifier is selected.
        assert connection_dialog.get_selected_connection() is True
        # The dictionary of the selected connection should be the pre-defined connection dictionary.
        assert connection_dialog.selected_connection_parameters_dictionary == connection_dictionary

        # Clean up, so the test connection is no longer part of the connection store.
        global_connection_store.delete_connection(connection_dictionary)
        global_connection_store.commit_current_list_to_yaml()

    def test_valid_delete_selected_connection(self):
        """
        Test the method for deleting the selected database connection with a saved database connection.
        """

        # Define a connection dictionary for saving the connection data in the connection store and creating a
        # connection identifier later, so the connection is part of the list widget and can be selected.
        connection_dictionary = {"Host": "random",
                                 "Username": "testuser",
                                 "Port": 5432,
                                 "Database": "postgres"}

        # Define a password identifier for setting a password, so it can be deleted.
        password_identifier = "{}@{}:{}".format(connection_dictionary["Username"], connection_dictionary["Host"],
                                                connection_dictionary["Port"])

        keyring.set_password("Pygadmin", password_identifier, "test")

        # Save the connection in the connection store.
        global_connection_store.save_connection_parameters_in_yaml_file(connection_dictionary)
        # Save the current connections in the connection store in the yaml file.
        global_connection_store.commit_current_list_to_yaml()

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Clean up, so the test connection is no longer part of the connection store.
        global_connection_store.delete_connection(connection_dictionary)
        global_connection_store.commit_current_list_to_yaml()

        # Define a connection identifier for selecting it in the list widget.
        connection_identifier = "{}@{}:{}/{}".format(connection_dictionary["Username"], connection_dictionary["Host"],
                                                     connection_dictionary["Port"], connection_dictionary["Database"])

        # Select the item related to the connection identifier.
        connection_dialog.find_occurrence_in_list_widget_and_select_item(connection_identifier)

        # The deletion of the selected connection should return True.
        assert connection_dialog.delete_selected_connection() is True

    def test_invalid_delete_selected_connection(self):
        """
        Test the method for deleting the selected database connection with an unsaved database connection.
        """

        # Define a connection dictionary for saving the connection data in the connection store and creating a
        # connection identifier later, so the connection is part of the list widget and can be selected.
        connection_dictionary = {"Host": "random",
                                 "Username": "testuser",
                                 "Port": 5432,
                                 "Database": "postgres"}

        # Save the connection in the connection store.
        global_connection_store.save_connection_parameters_in_yaml_file(connection_dictionary)
        # Save the current connections in the connection store in the yaml file.
        global_connection_store.commit_current_list_to_yaml()

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Clean up, so the test connection is no longer part of the connection store.
        global_connection_store.delete_connection(connection_dictionary)
        global_connection_store.commit_current_list_to_yaml()

        # Define a connection identifier for selecting it in the list widget.
        connection_identifier = "{}@{}:{}/{}".format(connection_dictionary["Username"], connection_dictionary["Host"],
                                                     connection_dictionary["Port"], connection_dictionary["Database"])

        # Select the item related to the connection identifier.
        connection_dialog.find_occurrence_in_list_widget_and_select_item(connection_identifier)

        # The deletion of the selected connection should not return True.
        assert connection_dialog.delete_selected_connection() is not True

    def test_check_for_valid_timeout(self):
        """
        Test the method for checking for a valid timeout.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Set the text to an empty string, so a cast to an integer is not possible.
        connection_dialog.timeout_line_edit.setText("")
        # The timeout should be invalid.
        assert connection_dialog.check_for_valid_timeout() is False

        # Set the text to an invalid integer value.
        connection_dialog.timeout_line_edit.setText("-42")
        # The timeout should still be invalid.
        assert connection_dialog.check_for_valid_timeout() is False

        # Set the text to a valid integer value.
        connection_dialog.timeout_line_edit.setText("42")
        # The result should now be True.
        assert connection_dialog.check_for_valid_timeout() is True

    def test_port_checkbox(self):
        """
        Test the correct behavior of the (de)activation of the checkbox for using the standard postgres port.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a dialog.
        connection_dialog = ConnectionDialogWidget()

        # Get the use postgres port checkbox of the dialog.
        postgres_port_checkbox = connection_dialog.use_postgres_port_checkbox
        # Get the port line edit.
        port_line_edit = connection_dialog.connection_parameter_edit_dictionary["Port"]

        # Set the checkbox unchecked.
        postgres_port_checkbox.setChecked(False)
        # Now the port line edit should be empty.
        assert port_line_edit.text() == ""

        # Define a port text for further testing.
        port_text = "1337"
        # Set the text as current text of the port line edit field.
        port_line_edit.setText(port_text)

        # Set the port checkbox to checked.
        postgres_port_checkbox.setChecked(True)
        # Now the port line edit should contain the standard postgres port as text.
        assert port_line_edit.text() == "5432"

        # Set the port checkbox back to unchecked.
        postgres_port_checkbox.setChecked(False)
        # Now the checkbox should contain the port text, which has been set earlier.
        assert port_line_edit.text() == port_text
