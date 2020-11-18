import unittest

import psycopg2

from pygadmin.connectionfactory import global_connection_factory


class TestConnectionFactoryMethods(unittest.TestCase):
    """
    Test the methods and the functionality of the (global) connection factory.
    """

    def test_factory_structure(self):
        """
        Check the data structure of the factory: The factory should use a dict for saving the internal connection data.
        """

        assert isinstance(global_connection_factory.connections_dictionary, dict)

    def test_valid_get_connection(self):
        """
        Use valid connection parameters for getting a correct connection.
        """

        connection = global_connection_factory.get_database_connection("localhost", "testuser", "testdb", 5432, 10000)

        assert isinstance(connection, psycopg2.extensions.connection)

    def test_wrong_password_get_connection(self):
        """
        Use a non existing user for testing a fail in the password storage, so the connection should be set to None.
        """

        connection = global_connection_factory.get_database_connection("localhost", "test", "testdb")

        assert connection is None

    def test_invalid_get_connection(self):
        """
        Use invalid connection parameters with an invalid/a non existing database, so the connection should be set to
        False.
        """

        connection = global_connection_factory.get_database_connection("localhost", "testuser", "test")

        assert connection is False

    def test_valid_get_parameters(self):
        """
        Test the method for getting parameters based on a given database connection. Predefine a dictionary with
        parameters, get the connection based on them and then, get the dictionary for the connection.
        """

        # Define database connection parameters in a dictionary. The structure is equivalent to the structure of the
        # dictionary, which is returned by the function of the factory for a connection.
        database_parameters = {
            "host": "localhost",
            "user": "testuser",
            "database": "testdb",
            "port": 5432,
        }

        # Get a database connection.
        connection = global_connection_factory.get_database_connection(database_parameters["host"],
                                                                       database_parameters["user"],
                                                                       database_parameters["database"],
                                                                       database_parameters["port"])

        # Get a dictionary based on the established connection.
        factory_parameters = global_connection_factory.get_database_connection_parameters(connection)

        # The dictionary, which was used to create a connection, and the dictionary, which matches with the connection,
        # should be equivalent.
        assert database_parameters == factory_parameters

    def test_invalid_get_parameters(self):
        """
        Test the method for getting connection parameters based on a connection with an invalid connection.
        """

        # Use None as database connection, which is obviously not a valid database connection.
        factory_parameter = global_connection_factory.get_database_connection_parameters(None)

        # For an error case, the method should return None.
        assert factory_parameter is None

    def test_valid_connection_test(self):
        """
        Use the method of the factory for testing a database connection with valid database connection parameters.
        """

        # A password is required for testing. Because this is a pure test environment and the data is more or less
        # random and the database is localhost, the password is hard coded and visible in this file.
        connection_possible = global_connection_factory.test_parameters_for_database_connection("localhost", "testuser",
                                                                                                "testdb", "test1234")

        # A correct connection should return True.
        assert connection_possible is True

    def test_invalid_connection_test(self):
        """
        Use the method of the factory for testing a database connection with invalid database connection parameters.
        """

        # Use invalid database connection parameters with an incorrect password.
        connection_possible = global_connection_factory.test_parameters_for_database_connection("localhost", "testuser",
                                                                                                "test", "test42")

        print(connection_possible)

        # An invalid connection should return False.
        assert connection_possible is False

    def test_valid_close_connection(self):
        """
        Test the correct close and delete mechanism for a database connection.
        """

        # Get a database connection.
        connection = global_connection_factory.get_database_connection("localhost", "testuser", "testdb")
        # Close the connection and get the boolean for closing.
        connection_closed = global_connection_factory.close_and_remove_database_connection(connection)

        # Check the boolean for closing.
        assert connection_closed is True
        # Double check: Try to find the connection parameters, which are related to the database connection. They should
        # be None for not found.
        assert global_connection_factory.get_database_connection_parameters(connection) is None

    def test_invalid_close_connection(self):
        """
        Test the close and delete mechanism for an invalid database connection.
        """

        # Try to close an invalid database connection.
        connection_closed = global_connection_factory.close_and_remove_database_connection(None)

        # The result should be not True.
        assert connection_closed is not True

    def test_connection_reestablish(self):
        """
        Test the method for reestablishing a database connection.
        """

        # Define database connection parameters for establishing a connection.
        database_parameters = {
            "host": "localhost",
            "user": "testuser",
            "database": "testdb",
            "port": 5432,
        }

        # Get the first connection related to the given parameters.
        connection = global_connection_factory.get_database_connection(database_parameters["host"],
                                                                       database_parameters["user"],
                                                                       database_parameters["database"],
                                                                       database_parameters["port"])

        # Use the database parameters for creating a new connection, which is the reestablished old connection.
        new_connection = global_connection_factory.reestablish_terminated_connection(database_parameters)

        # The old connection should be closed, so the closed attribute should be 1.
        assert connection.closed == 1
        # Try to get connection parameters related to the old connection. This should be None, because a match is not
        # found.
        assert global_connection_factory.get_database_connection_parameters(connection) is None
        # The new connection should be open, so the attribute should be 0.
        assert new_connection.closed == 0
        # Check for the related connection parameters, which should be the initial dictionary.
        assert global_connection_factory.get_database_connection_parameters(new_connection) == database_parameters

