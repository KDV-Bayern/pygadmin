import unittest
import os

from pygadmin.connectionstore import global_connection_store


class TestConnectionStoreMethods(unittest.TestCase):
    """
    Test the connection store with its method and its behavior.
    """

    def test_path_of_connection_file(self):
        """
        Test the existence of the file for storing the connection parameters.
        """

        assert os.path.exists(global_connection_store.yaml_connection_parameters_file)

    def test_connection_list(self):
        """
        Test the connection list for its correct instance, which is also an implicit test for its existence.
        """

        assert isinstance(global_connection_store.connection_parameters_yaml, list)

    def test_get_connection_parameters(self):
        """
        Test the function for getting all connection parameters.
        """

        # Use the function for getting the list.
        connection_parameter_list = global_connection_store.get_connection_parameters_from_yaml_file()
        # Check, if the returned list is the one, which contains all connection parameters in the connection store.
        assert connection_parameter_list == global_connection_store.connection_parameters_yaml

    def test_valid_save_connection_parameters(self):
        """
        Test the function for saving connection parameters with valid paramters.
        """

        # Define valid parameters.
        test_parameters = {"Host": "testhost",
                           "Username": "testuser",
                           "Database": "testdb",
                           "Port": 5432}

        # Save the parameters and assume a result, which is True.
        assert global_connection_store.save_connection_parameters_in_yaml_file(test_parameters) is True

        # Use a clean up with deleting the connection.
        global_connection_store.delete_connection(test_parameters)

    def test_invalid_save_connection_parameters(self):
        """
        Test the function for saving connection parameters with invalid parameters.
        """

        # Use an empty dictionary as invalid parameters.
        assert global_connection_store.save_connection_parameters_in_yaml_file({}) is False

    def test_duplicate_check(self):
        """
        Test the function for a duplicate check.
        """

        # Define test parameters.
        test_parameters = {"Host": "testhost",
                           "Username": "testuser",
                           "Database": "testdb",
                           "Port": 1337}

        # Save the parameters in the connection store and yaml file.
        global_connection_store.save_connection_parameters_in_yaml_file(test_parameters)

        # Use the function for checking a duplicate with the test parameters again.
        assert global_connection_store.check_parameter_for_duplicate(test_parameters) is True

        # Clean up.
        global_connection_store.delete_connection(test_parameters)

    def test_valid_delete_connection(self):
        """
        Test the function for deleting a connection with saving parameters first and then deleting them.
        """

        # Define test parameters.
        test_parameters = {"Host": "testhost",
                           "Username": "testuser",
                           "Database": "testdb",
                           "Port": 1337}

        # Save the parameters.
        global_connection_store.save_connection_parameters_in_yaml_file(test_parameters)

        # Delete the parameters and assume a successful deletion.
        assert global_connection_store.delete_connection(test_parameters) is True

    def test_invalid_delete_connection(self):
        """
        Test the deletion of an invalid connection dictionary.
        """

        # Use an empty dictionary as invalid dictionary.
        assert global_connection_store.delete_connection({}) is False

    def test_valid_change_connection(self):
        """
        Test the change of a connection with a valid connection dictionary and a new dictionary with changed paramters.
        """

        # Define the first test parameters.
        test_parameters = {"Host": "testhost",
                           "Username": "testuser",
                           "Database": "testdb",
                           "Port": 1337}

        # Save the first parameters.
        global_connection_store.save_connection_parameters_in_yaml_file(test_parameters)

        # Define changed parameters with a different port.
        changed_test_parameters = {"Host": "testhost",
                                   "Username": "testuser",
                                   "Database": "testdb",
                                   "Port": 5432}

        # Test for the correct change of parameters.
        assert global_connection_store.change_connection(test_parameters, changed_test_parameters) is True

        # Clean up.
        global_connection_store.delete_connection(changed_test_parameters)

    def test_invalid_change_connection(self):
        """
        Test the function for changing information about a connection with invalid/duplicate data.
        """

        # Define a dictionary with connection parameters.
        test_parameters = {"Host": "testhost",
                           "Username": "testuser",
                           "Database": "testdb",
                           "Port": 1337}

        # Save the connection.
        global_connection_store.save_connection_parameters_in_yaml_file(test_parameters)

        # Try to change the connection information, but this test should return False, because it is a duplicate.
        assert global_connection_store.change_connection(test_parameters, test_parameters) is False

        # Clean up.
        global_connection_store.delete_connection(test_parameters)

    def test_valid_check_key(self):
        """
        Test the method for checking for the correct keys in the connection dictionary with valid data.
        """

        # Define a dictionary with test parameters.
        test_parameters = {"Host": "testhost",
                           "Username": "testuser",
                           "Database": "testdb",
                           "Port": 1337}

        # Assume a success.
        assert global_connection_store.check_for_correct_keys_in_dictionary(test_parameters) is True

    def test_invalid_check_key(self):
        """
        Test the method for checking for the correct keys in the dictionary with invalid data.
        """

        # Use an empty dictionary as invalid data.
        assert global_connection_store.check_for_correct_keys_in_dictionary({}) is False

    def test_connection_parameter_number(self):
        """
        Test the method for getting the number of connection parameters.
        """

        # Get the length of the list with parameters and compare them with the result of the method.
        assert len(global_connection_store.connection_parameters_yaml) \
               == global_connection_store.get_number_of_connection_parameters()

    def test_valid_index_of_connection(self):
        """
        Test the method for getting the index of a connection with a known dictionary and valid data.
        """

        # Get the current number of connection parameters before adding new data.
        current_parameters_number = global_connection_store.get_number_of_connection_parameters()

        # Define a test dictionary.
        test_parameters = {"Host": "testhost",
                           "Username": "testuser",
                           "Database": "testdb",
                           "Port": 1337}

        # Save the test dictionary.
        global_connection_store.save_connection_parameters_in_yaml_file(test_parameters)

        # Check for the correct index of the new connection.
        assert global_connection_store.get_index_of_connection(test_parameters) == current_parameters_number

        # Clean up.
        global_connection_store.delete_connection(test_parameters)

    def test_invalid_index_of_connection(self):
        """
        Test the method for getting the index of a connection with invalid data and as a result an invalid index.
        """

        # Use an empty dictionary as invalid data.
        assert global_connection_store.get_index_of_connection({}) is None

    def test_valid_connection_at_index(self):
        """
        Test the method for getting an index at a specified position.
        """

        # Define test parameters.
        test_parameters = {"Host": "testhost",
                           "Username": "testuser",
                           "Database": "testdb",
                           "Port": 1337}

        # Save the parameters.
        global_connection_store.save_connection_parameters_in_yaml_file(test_parameters)

        # After a save of parameters, there has to be a connection at index 0.
        connection_at_index = global_connection_store.get_connection_at_index(0)

        # Check the connection for the right instance.
        assert isinstance(connection_at_index, dict)
        # Check the connection for the correct keys, so the data structure is correct.
        assert "Host" in connection_at_index
        assert "Username" in connection_at_index
        assert "Database" in connection_at_index
        assert "Port" in connection_at_index

        # Clean up.
        global_connection_store.delete_connection(test_parameters)

    def test_invalid_connection_at_index(self):
        """
        Test the method for getting a connection at a given index with invalid data.
        """

        # Get the current number of connections.
        current_connection_number = global_connection_store.get_number_of_connection_parameters()
        # Check for the current number of connection as index (which is None, because the index starts at 0).
        assert global_connection_store.get_connection_at_index(current_connection_number) is None

