import os
import subprocess
import tempfile
import re
import keyring
import logging

from pygadmin.configurator import global_app_configurator


class DatabaseDumper:
    """
    Create a class, which is responsible for and capable of database dumps. This class is required for getting the
    create statement of a database.
    """

    def __init__(self, user, database, host, port, dump_information, information_name=None):
        """
        Get the relevant parameters, which specify the connection and the database for a dump. The dump information
        contains the type of information for the dump, so this includes databases, tables and views. The information
        name contains the name of the view or table.
        """

        self.user = user
        self.database = database
        self.host = host
        self.port = port
        self.dump_information = dump_information
        self.information_name = information_name
        self.pg_dump_statement = None
        self.service_name = "Pygadmin"
        # Define a pg dump path as None, so the path can be set later.
        self.pg_dump_path = None

    def dump_database(self):
        """
        Dump the database with a previous check for a password. Use a password file for submitting the password for the
        dump, which is specified in the environment variable for the PGPASSFILE.
        """

        # Create a password identifier out of the username, host and port for checking the password for this identifier
        # in the keyring.
        password_identifier = "{}@{}:{}".format(self.user, self.host, self.port)

        # If the password in the keyring is not None, proceed. If the password were None, there would be a missing
        # password for the given identifier. The password is necessary for the following steps.
        if keyring.get_password(self.service_name, password_identifier) is not None:
            # Create a temporary pass file and get the file handler and path.
            file_handler, file_path = self.create_pass_file(password_identifier)

            # Get a copy of the current process environment with its specified variables as a dictionary.
            process_env = os.environ.copy()
            # Set the file path of the created file as PGPASSFILE.
            process_env['PGPASSFILE'] = file_path

            # Get the path of the pg_dump executable.
            self.get_pg_dump_path()

            # Get the statement for the dump.
            self.get_pg_dump_statement()

            # Define a variable for the result, which is returned later.
            result = None

            # Try to dump the database.
            try:
                # Use a subprocess for the dump. Use the pg_dump statement and capture the output. The environment is
                # set as predefined process environment, which contains a PGPASSFILE. A timeout is set, so after 30
                # seconds, the subprocess is canceled. stdout defines the output place and is used for Python 3.6
                # compatibility. Universal newlines are used for a more "beautiful" output.
                result = subprocess.run(self.pg_dump_statement, env=process_env, timeout=30, stdout=subprocess.PIPE,
                                        universal_newlines=True)

            # If an exception occurs, for example triggered by a timeout, save a message in the log.
            except Exception as error:
                logging.error("An error occurred during the dumping process: {}".format(error), exc_info=True)

            # Use a finally block for a short clean up.
            finally:
                # Try to remove the file. Use a try statement, because this block can cause errors for windows user.
                try:
                    # Remove the file, which was used for submitting the password and is no longer necessary.
                    os.remove(file_path)

                # Add the exception to the log.
                except Exception as error:
                    logging.error("An error occurred during the clean up process of the database dump: {}".format(
                        error), exc_info=True)

                # Return the result.
                return result

    def create_pass_file(self, password_identifier):
        """
        Get the password identifier and create a pass file, which is used for the login process in pg_dump.
        """

        # Create a secure temporary file with a file handler and a path.
        file_handler, file_path = tempfile.mkstemp()

        # Open the file with its path in the writing mode.
        with open(file_path, "w") as file:
            # Write the relevant data for a pass file into the file. This construction is recommended by the
            # documentation of PostgreSQL.
            file.write("{}:{}:{}:{}:{}".format(self.host, self.port, self.database, self.user,
                                               keyring.get_password(self.service_name, password_identifier)))

        # Return the information about the temporary file.
        return file_handler, file_path

    def get_pg_dump_path(self):
        """
        Get the path for the executable pg_dump out of the configuration file. Check the path for its existence.
        """

        # Get the path out of the configuration file.
        pg_dump_path = global_app_configurator.get_single_configuration("pg_dump_path")

        # Check for the existence of the path. The path is None, if there is no such configuration. If there is a path,
        # check for its existence with os.
        if pg_dump_path is not None and os.path.exists(pg_dump_path):
            # Use the given path as executable.
            self.pg_dump_path = pg_dump_path

        # If the pg_dump path does not exist or cannot be found, use the default pg_dump.
        else:
            self.pg_dump_path = "pg_dump"

    def get_pg_dump_statement(self):
        """
        Get the pg_dump statement based on the type of dump information. The statement for getting the create statement
        of a database contains different arguments compared to the arguments for the create statement of a table or
        view.
        """

        # Create the statement for a database.
        if self.dump_information == "Database":
            # Exclude all tables and views with their specific information.
            table_view_statement = '-T*'
            # Show the create statement of the database.
            create_statement = '--create'

        # Create the statement for a table or view.
        else:
            # Define the name of the table or view. The parameter --table includes views, materialized views, sequences,
            # and foreign tables in this case according to the documentation of pg_dump.
            table_view_statement = "--table={}".format(self.information_name)
            # Exclude the data in the tables, so only the schema is dumped.
            create_statement = '--schema-only'

        # Create a connection identifier for the usage in the pg_dump statement.
        connection_identifier = "postgresql://{}@{}:{}/{}".format(self.user, self.host, self.port, self.database)

        # Define the different parameters for the dump. First, there is the call of the pre defined pg_dump
        # executable, followed by the parameter with the table specifications. The create statement contains the
        # parameter for the definition without data.
        self.pg_dump_statement = [self.pg_dump_path, table_view_statement, create_statement, '--dbname={}'.format(
            connection_identifier)]

    def dump_database_and_clean_result(self):
        """
        Dump the database with the function for dumping the database and clean the result, so the result contains the
        relevant data in a list. The relevant data is based on the dump information.
        """

        # Dump the database.
        dump_result = self.dump_database()

        # Check, if the dump result is not None, so there was a successful dump.
        if dump_result is not None:
            # Get the result of the dump in separate lines in a list.
            dump_result_lines = dump_result.stdout.split(os.linesep)

            # If the dump is used for the create statement of a database, use the function for cleaning the result  for
            # a database.
            if self.dump_information == "Database":
                return self.clean_database_result(dump_result_lines)

            # Use the function for cleaning a table result, if the relevant information is for a table.
            elif self.dump_information == "Table":
                return self.clean_table_result(dump_result_lines)

            # Use the function for cleaning a table result, if the relevant information is for a table.
            elif self.dump_information == "View":
                return self.clean_view_result(dump_result_lines)

    @staticmethod
    def clean_database_result(dump_result_line_list):
        """
        Clean the results, which are used for the create statement of a database.
        """

        # If the dump result line list has the wrong type, return None.
        if not isinstance(dump_result_line_list, list):
            return None

        # Define an empty list for the results.
        cleaned_result_lines = []

        # Check every line.
        for line in dump_result_line_list:
            # Check, if the line contains a CREATE or ALTER as relevant information for a CREATE DATABASE
            # statement.
            if re.search("CREATE|ALTER", line):
                # Append a match to the result list.
                cleaned_result_lines.append(line)

        return cleaned_result_lines

    @staticmethod
    def clean_table_result(dump_result_line_list):
        """
        Clean the results, which are used for the create statement of a table. The number of open and closed brackets is
        relevant for these information.
        """

        # Return None the wrong type.
        if not isinstance(dump_result_line_list, list):
            return None

        # Define a variable for the results.
        cleaned_result_lines = []
        # Define a variable for the bracket count. This is like a non-empty stack. The variable is incremented for a (
        # and decremented for a ), so if the number of ( is equal to the number of ), the create statement ends.
        bracket_count = 0

        # Check every line.
        for line in dump_result_line_list:
            # Search for a CREATE TABLE or check the bracket count.
            if re.search("CREATE TABLE", line) or bracket_count != 0:
                # Append the result in a more readable way.
                cleaned_result_lines.append(line + "\n")

                # Check every character in the line for an occurrence of ( or )
                for character in line:
                    # If the line contains a (, increment.
                    if character == "(":
                        bracket_count += 1

                    # If the line contains a ), decrement.
                    if character == ")":
                        bracket_count -= 1

        return cleaned_result_lines

    @staticmethod
    def clean_view_result(dump_result_line_list):
        """
        Clean the results, which are used for the create statement of a table. The create view statement does not
        contain brackets, so after a CREATE VIEW, there is the check for a semicolon.
        """

        #  Return None for the wrong instance of the input list.
        if not isinstance(dump_result_line_list, list):
            return None

        # Define a list for the results.
        cleaned_result_lines = []
        # Create a variable, which is set to True for the first occurrence of CREATE VIEW.
        create_view = False

        # Check every line.
        for line in dump_result_line_list:
            # Search CREATE VIEW or proceed for after the variable for create view is set to True, so a create view
            # statement begins, but it has not reached the end.
            if re.search("CREATE VIEW", line) or create_view is True:
                # Append the line in a more readable way.
                cleaned_result_lines.append(line + "\n")
                # Create view is reached or should be continue, because the statement has not reached the end.
                create_view = True

                # Check every line for a semicolon.
                for character in line:
                    if character == ";":
                        # Set the create view boolean to False, so the loop ends, because the statement ends.
                        create_view = False

        return cleaned_result_lines
