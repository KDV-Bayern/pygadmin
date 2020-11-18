import os
import re
import unittest

from pygadmin.database_dumper import DatabaseDumper
from pygadmin.configurator import global_app_configurator


class TestDatabaseDumperMethods(unittest.TestCase):
    """
    Test the class for dumping a database and its behavior.
    """

    def test_valid_database_dump(self):
        """
        Use valid data for dumping a database and get the result.
        """

        # Use a valid connection and valid dump data.
        database_dumper = DatabaseDumper("testuser", "testdb", "localhost", 5432, "Table", "test")
        # Get the result of a database dump.
        result = database_dumper.dump_database()

        assert result is not None

    def test_invalid_database_dump(self):
        """
        Use invalid data for dumping a database and check the invalid result.
        """

        # Use an invalid connection and invalid dump data.
        database_dumper = DatabaseDumper("testuser", "testdb", "localhost", 1337, "Table", "test")
        # Get the result of a database dump.
        result = database_dumper.dump_database()

        assert result is None

    def test_valid_create_pass_file(self):
        """
        Test the method for creating a pass file with valid data.
        """

        # Define the relevant data for a dump.
        user = "testuser"
        database = "testdb"
        host = "localhost"
        port = 5432
        dump_information = "Table"
        table_name = "test"

        # Define a password identifier, which is relevant for the creating of a pass file.
        password_identifier = "{}@{}:{}".format(user, host, port)

        # Create a dumper.
        database_dumper = DatabaseDumper(user, database, host, port, dump_information, table_name)

        # Get the file path and handler.
        file_path, file_handler = database_dumper.create_pass_file(password_identifier)

        # Check the file path and the file handler for its existence.
        assert os.path.exists(file_path) is True
        assert os.path.exists(file_handler) is True

    def test_invalid_create_pass_file(self):
        """
        Test the creation and usage of a pass file with invalid data, so the host, user and port cannot be found in the
        password manager. The file creation and usage should function normally.
        """

        # Define the relevant data for a dump.
        user = "testasdf"
        database = "testdb"
        host = "unknown"
        port = 1337
        dump_information = "Table"
        table_name = "test"

        # Define a password identifier, which is relevant for the creating of a pass file.
        password_identifier = "{}@{}:{}".format(user, host, port)

        # Create a dumper.
        database_dumper = DatabaseDumper(user, database, host, port, dump_information, table_name)

        # Get the file path and handler.
        file_path, file_handler = database_dumper.create_pass_file(password_identifier)

        # Check the file path and the file handler for its existence, because they should also exist for invalid data.
        assert os.path.exists(file_path) is True
        assert os.path.exists(file_handler) is True

    def test_pg_dump_path(self):
        """
        Test the functionality of the method for getting the pg dump path with also checking for the path in the global
        app configurator.
        """

        # Get the pg dump path out of the global app configurator.
        configurator_dump_path = global_app_configurator.get_single_configuration("pg_dump_path")

        # Create a dumper.
        database_dumper = DatabaseDumper("testuser", "testdb", "localhost", 5432, "Table", "test")
        # Get the dump path as accessible attribute of the class.
        database_dumper.get_pg_dump_path()

        # If a path in the configurator does exist, check for the correct set.
        if configurator_dump_path is not None and os.path.exists(configurator_dump_path):
            # The path in the configurator should be the pg dump path of the dumper.
            assert database_dumper.pg_dump_path == configurator_dump_path

        # The path should not be a None, so it has been set.
        assert database_dumper.pg_dump_path is not None

    def test_database_pg_dump_statement(self):
        """
        Test the creation of a pg dump statement for a database.
        """

        # Define the relevant parameters as local variables.
        user = "testuser"
        database = "testdb"
        host = "localhost"
        port = 5432
        dump_information = "Database"
        information_name = "testdb"

        # Create a dumper.
        database_dumper = DatabaseDumper(user, database, host, port, dump_information, information_name)
        # Get the dump path as attribute of the dumper, which is necessary for the dump statement.
        database_dumper.get_pg_dump_path()
        # Get the dump statement as attribute of the dumper.
        database_dumper.get_pg_dump_statement()

        # The statement is a list, so get the list.
        statement_list = database_dumper.pg_dump_statement

        # Check for the correct instance of the list.
        assert isinstance(statement_list, list)
        # Check for the relevant strings and statements as part of the statement list.
        assert database_dumper.pg_dump_path in statement_list
        assert "-T*" in statement_list
        assert "--create" in statement_list
        assert "--dbname=postgresql://{}@{}:{}/{}".format(user, host, port, database) in statement_list

    def test_table_pg_dump_statement(self):
        """
        Test the creation of a pg dump statement for a table.
        """

        # Define the relevant parameters as local variables.
        user = "testuser"
        database = "testdb"
        host = "localhost"
        port = 5432
        dump_information = "Table"
        information_name = "test"

        # Create a dumper.
        database_dumper = DatabaseDumper(user, database, host, port, dump_information, information_name)
        # Get the dump path as attribute of the dumper, which is necessary for the dump statement.
        database_dumper.get_pg_dump_path()
        # Get the dump statement as attribute of the dumper.
        database_dumper.get_pg_dump_statement()

        # The statement is a list, so get the list.
        statement_list = database_dumper.pg_dump_statement

        # Check for the correct instance of the list.
        assert isinstance(statement_list, list)
        # Check for the relevant strings and statements as part of the statement list.
        assert database_dumper.pg_dump_path in statement_list
        assert "--table={}".format(information_name) in statement_list
        assert "--schema-only" in statement_list
        assert "--dbname=postgresql://{}@{}:{}/{}".format(user, host, port, database) in statement_list

    def test_valid_database_dump_clean_result(self):
        """
        Test the dump of a database with valid data and test the clean of the result.
        """

        # Use a valid connection and valid dump data.
        database_dumper = DatabaseDumper("testuser", "testdb", "localhost", 5432, "Table", "test")
        # Get the result of a database dump.
        result = database_dumper.dump_database_and_clean_result()

        # The result should be a list.
        assert isinstance(result, list)

    def test_invalid_database_dump_clean_result(self):
        """
        Test the dump of a database with invalid data and test the clean of the result.
        """

        # Use an invalid connection and invalid dump data.
        database_dumper = DatabaseDumper("testuser", "testdb", "localhost", 1337, "Table", "test")
        # Get the result of a database dump.
        result = database_dumper.dump_database()

        assert result is None

    def test_clean_database_result(self):
        """
        Test the clean of the database result.
        """

        # Use a valid connection and valid dump data.
        database_dumper = DatabaseDumper("testuser", "testdb", "localhost", 5432, "Database", "testdb")
        # Get the result of a database dump.
        result = database_dumper.dump_database()
        # Split the result into lines.
        result_lines = result.stdout.split(os.linesep)
        # Clean the result.
        result_list = database_dumper.clean_database_result(result_lines)

        # Check for the correct clean, so only lines with CREATE or ALTER are valid.
        for line in result_list:
            assert re.search("CREATE|ALTER", line) is not None

    def test_clean_table_result(self):
        """
        Test the clean of the table result.
        """

        # Use a valid connection and valid dump data.
        database_dumper = DatabaseDumper("testuser", "testdb", "localhost", 5432, "Table", "test")
        # Get the result of a database dump.
        result = database_dumper.dump_database()
        # Split the result into lines.
        result_lines = result.stdout.split(os.linesep)
        # Clean the table result.
        result_list = database_dumper.clean_table_result(result_lines)
        # Define a bracket count, which counts opened and closed brackets.
        bracket_count = 0

        # Check every line for a CREATE or open/closed brackets.
        for line in result_list:
            assert re.search("CREATE", line) or bracket_count != 0
            for character in line:
                if character == "(":
                    bracket_count += 1

                if character == ")":
                    bracket_count -= 1

    def test_clean_view_result(self):
        """
        Test the clean of a view result.
        """

        # Use a valid connection and valid dump data.
        database_dumper = DatabaseDumper("testuser", "testdb", "localhost", 5432, "View", "testview")
        # Get the result of a database dump.
        result = database_dumper.dump_database()
        # Split the result into lines.
        result_lines = result.stdout.split(os.linesep)
        # Clean the table result
        result_list = database_dumper.clean_view_result(result_lines)
        # This line is set to True after a CREATE VIEW and is set to False after a semicolon, which ends the command.
        create_view = False

        # Check the result lines.
        for line in result_list:
            # The line should contain a CREATE VIEW or the create view should be in a previous line.
            assert re.search("CREATE VIEW", line) or create_view is True

            create_view = True

            # Check for a semicolon to end the command.
            for character in line:
                if character == ";":
                    create_view = False

    def test_invalid_clean_result(self):
        # Use a valid connection and valid dump data.
        database_dumper = DatabaseDumper("testuser", "testdb", "localhost", 5432, "Database", "testdb")

        database_dumper.clean_database_result(None)

