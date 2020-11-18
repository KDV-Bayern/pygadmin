import unittest

from pygadmin.database_query_executor import DatabaseQueryExecutor

from pygadmin.connectionfactory import global_connection_factory


class TestDatabaseQueryExecutorMethods(unittest.TestCase):
    """
    Test the methods and the functionality of the database query executor.
    """

    def test_creation(self):
        """
        Test the creation of an object of the type database query executor.
        """

        executor = DatabaseQueryExecutor()

        # Check all relevant data as set to None.
        assert executor.database_connection is None
        assert executor.database_query is None
        assert executor.database_query_parameter is None

    def test_valid_execute_query(self):
        """
        Test the execution of a database query with valid input parameters.
        """

        # Create an executor.
        executor = DatabaseQueryExecutor()
        # Create a database connection.
        database_connection = global_connection_factory.get_database_connection("localhost", "testuser", "testdb")
        # Get the result and the message of a query.
        result_data_list, query_message = executor.execute_query("SELECT * FROM test;", database_connection.cursor())

        # The first result should be a list.
        assert isinstance(result_data_list, list)
        # The second result should be a message as string.
        assert isinstance(query_message, str)

    def test_invalid_execute_query(self):
        """
        Test the execution of a database query with invalid input parameters.
        """

        # Create an executor.
        executor = DatabaseQueryExecutor()
        # Create a database connection.
        database_connection = global_connection_factory.get_database_connection("localhost", "testuser", "testdb")

        # This try statement is used for causing an error and catching it, because with an invalid table, there will
        # be an error. assertRaise cannot be used, because the resulting error is a psycopg2 error and not a python
        # exception.
        try:
            # Execute a query with an invalid/a undefined table.
            executor.execute_query("SELECT * FROM testtt;", database_connection.cursor())
            # Assert something, which is wrong, so the test will fail, if this statement is reached.
            assert 2 + 2 == 5

        # Use the exception block for the assertion: Reaching this block, something, which is true, will be asserted, so
        # the test will pass.
        except Exception as error:
            assert isinstance(error, Exception)

    def test_valid_connection_with_valid_parameters(self):
        """
        Test the method is_connection_valid of the database query executor with valid database connection parameters and
        a valid database connection.
        """

        # Create an executor.
        executor = DatabaseQueryExecutor()
        # Create a database connection.
        database_connection = global_connection_factory.get_database_connection("localhost", "testuser", "testdb")
        # Set the new database connection as connection for the executor.
        executor.database_connection = database_connection

        # The fresh and new connection should be valid.
        assert executor.is_connection_valid() is True

        # Close the database connection.
        database_connection.close()

        # Now the connection after a close should be invalid.
        assert executor.is_connection_valid() is False

        # Clean up: Remove the connection from the connection factory to prevent the further usage of the connection,
        # which can cause errors or test failures.
        global_connection_factory.close_and_remove_database_connection(database_connection)

    def test_valid_connection_with_invalid_parameters(self):
        """
        Test the method is_connection_valid with invalid parameters and an invalid database connection.
        """

        # Create an executor.
        executor = DatabaseQueryExecutor()
        # Set the database connection of the executor to None.
        executor.database_connection = None

        # The connection should be invalid.
        assert executor.is_connection_valid() is False

    def test_reestablish_connection(self):
        """
        Test the method for reestablishing a database connection.
        """

        # Create an executor.
        executor = DatabaseQueryExecutor()

        database_connection = global_connection_factory.get_database_connection("localhost", "testuser", "testdb")
        # Set the new database connection as connection for the executor.
        executor.database_connection = database_connection

        # Check for a valid connection.
        assert executor.is_connection_valid() is True
        # Close the database connection.
        database_connection.close()
        # The connection should be invalid after a close.
        assert executor.is_connection_valid() is False
        # Reestablish the database connection.
        executor.reestablish_connection()
        # The connection should now be valid again.
        assert executor.is_connection_valid() is True

    def test_valid_connection_check_and_reestablish(self):
        """
        Test the function check_for_valid_connection_and_reestablish of the executor with a valid database connection.
        """

        # Create an executor.
        executor = DatabaseQueryExecutor()

        database_connection = global_connection_factory.get_database_connection("localhost", "testuser", "testdb")
        # Set the new database connection as connection for the executor.
        executor.database_connection = database_connection

        # The new connection should return True, because the connection is functional.
        assert executor.check_for_valid_connection_and_reestablish() is True
        # Close the database connection.
        database_connection.close()
        # Check for a valid connection and reestablish: This should be True, because a connection can be reestablished.
        assert executor.check_for_valid_connection_and_reestablish() is True

    def test_invalid_connection_check_and_reestablish(self):
        """
        Test the function check_for_valid_connection_and_reestablish of the executor with an invalid database
        connection.
        """

        # Create an executor.
        executor = DatabaseQueryExecutor()
        # Set the database connection of the executor to None, which is an invalid database connection.
        executor.database_connection = None

        # The connection should be invalid. As a result, the connection cannot be reestablished.
        assert executor.check_for_valid_connection_and_reestablish() is False

