import psycopg2
import keyring
import logging
import re


class ConnectionFactory:
    """
    Create a class for administration of connections used in the application. The class saves a connection as a value
    with its identifier as key, which is based on the given user, the given host and the given database.
    """

    def __init__(self):
        self.connections_dictionary = {}
        self.service_name = "Pygadmin"

    def get_database_connection(self, host, user, database, port=5432, timeout=10000):
        """
        Establish a database connection based on a given host, user, database and port, which is mostly port 5432. Use a
        timeout, so after this time, a query is cancelled. If there is already a connection for the specific identifier
        in the connection dictionary, use the connection. If there is none, establish a new one.
        """

        # A connection identifier is used as a unique key to identify a user on a specific server and database.
        connection_identifier = "{}@{}:{}/{}".format(user, host, port, database)
        # Create a password identifier for recognizing the database connection in the password manager. It is not
        # necessary to specify the database. So the connection identifier is split at the slash. The database follows
        # after the slash, so the first item of the split is taken as password identifier.
        password_identifier = connection_identifier.split("/")[0]

        # If a connection identifier exists in the connection dictionary, there is not need for establishing a new
        # connection.
        if connection_identifier in self.connections_dictionary:
            # Get the connection by its key, the connection identifier.
            database_connection = self.connections_dictionary[connection_identifier]

        # This elif branch is used for error handling in one specific case. If the check for a password for a user
        # returns None, the user is unknown in the password manager.
        elif keyring.get_password(self.service_name, password_identifier) is None:
            # Set the database connection to None as a part of error handling. There can be a case differentiation
            # between a database connection with the value None and the value False.
            database_connection = None

            logging.error("Identifier {} unknown in the password manager.".format(password_identifier))

        else:
            # Use a try except statement for potential psycopg2 errors while the connection is being established.
            try:
                # Use an url with the connection identifier for a connection.
                postgres_url = "postgresql://{}".format(connection_identifier)
                # Use an parameter for the connection with a timeout.
                timeout_description = "-c statement_timeout={}".format(timeout)
                # Establish a connection with the url, the password in the keyring and the timeout as option.
                database_connection = psycopg2.connect(postgres_url,
                                                       password=keyring.get_password(self.service_name,
                                                                                     password_identifier),
                                                       options=timeout_description)

                # Set the autocommit option to True, so changes are immediately, once a cursor is used.
                database_connection.autocommit = True

                # Save the connection in the dictionary for potential later use.
                self.connections_dictionary[connection_identifier] = database_connection

                logging.info("Connection with identifier {} established.".format(connection_identifier))

            except psycopg2.OperationalError as connection_error:
                # Set the database connection to False as a sign for an occurred error. Because .pgerror does not seem
                # to work, this is a general error. There are approximately 61 different problems causing this error.
                # A mapping is nearly impossible without the code because the error messages are translated to the
                # language of the system.
                database_connection = False
                logging.error("Connection with database {} failed. For further information, this exception occurred: "
                              "{}".format(database, connection_error), exc_info=True)

        # At this point, the database connection can contain a connection or a value with None or False. This makes
        # error handling possible in every function and objects, which uses this factory.
        return database_connection

    def get_database_connection_parameters(self, database_connection):
        """
        Use a given database connection to find the related database connection parameters. If one is found, get the
        database connection identifier and create a dictionary with the parameters and return it. If not, return None.
        """

        # Define a container for the results of the following statements.
        database_parameter_dictionary = None

        # Check every key and value pair in the dictionary, where all connections and their identifier are stored.
        for stored_database_connection_identifier, stored_database_connection in self.connections_dictionary.items():
            # Check if a stored connection is the given database connection.
            if stored_database_connection == database_connection:
                # Save the identifier of the found connection.
                database_connection_identifier = stored_database_connection_identifier
                # Create a list of the parameters out of the identifier. The identifier has three different characters
                # for separation, @, : and /. These lead to four different elements in the resulting list.
                parameter_list = [parameter.strip() for parameter in re.split("[@:/]", database_connection_identifier)]
                # Save the parameters in a dictionary.
                database_parameter_dictionary = {
                    "user": parameter_list[0],
                    "host": parameter_list[1],
                    # Cast the port to an integer for preventing weird behavior.
                    "port": int(parameter_list[2]),
                    "database": parameter_list[3]
                }

        return database_parameter_dictionary

    def test_parameters_for_database_connection(self, host, user, database, password, port=5432):
        """
        Test given database connection parameters for their validity, so they can used for a valid database connection.
        Check, if these parameters are already part of the dictionary and if they are, there is a valid connection. If
        not, try to establish a database connection.
        """

        # Create a connection identifier for establishing a connection.
        connection_identifier = "{}@{}:{}/{}".format(user, host, port, database)

        # Check for the identifier in the dictionary for all connections. If the identifier is found there as a key, the
        # connection is valid, because the dictionary contains all current valid connections.
        if connection_identifier in self.connections_dictionary:
            return True

        # Try to establish a database connection.
        try:
            # Create a postgres url, so not every parameters is separated as part for the connection.
            postgres_url = "postgresql://{}".format(connection_identifier)
            # Use the url and the password for a database connection.
            psycopg2.connect(postgres_url, password=password)

            # Congratulations, if this value is returned, the database connection is valid.
            return True

        # Use an except case, if the database connection failed.
        except psycopg2.OperationalError as database_error:
            # Save at least a specific error in den log.
            logging.error("Test database connection for identifier {} failed with the error {}".format(
                connection_identifier, database_error), exc_info=True)

            return False

    def close_and_remove_database_connection(self, database_connection):
        """
        Get a database connection and close this connection. Find also the corresponding identifier in the dictionary
        for deleting this identifier with its connection.
        """

        # Define a variable for the connection identifier match in the dictionary. After a checkup, this variable should
        # contain the connection identifier as key to the given database connection as value.
        connection_identifier_match = None

        # Check the dictionary with all connections with its keys and values as identifiers and connections.
        for connection_identifier, saved_database_connection in self.connections_dictionary.items():
            # Check for the given database in the dictionary.
            if saved_database_connection == database_connection:
                # Assign the connection identifier as key to the match variable.
                connection_identifier_match = connection_identifier

        # Check for a correct match.
        if connection_identifier_match is not None:
            # Close the given database connection.
            database_connection.close()
            # Remove the database connection from the dictionary with its identifier.
            del self.connections_dictionary[connection_identifier_match]
            # Save an information in the log.
            logging.info("Connection with identifier {} closed.".format(connection_identifier_match))

            # Return True for a success.
            return True

    def reestablish_terminated_connection(self, connection_parameters):
        """
        Get connection parameters and find the relevant database connection. Close the connection and reestablish a
        database connection. Return the new connection.
        """

        # Get the database connection out of the class-wide dictionary with the connection parameters.
        connection_in_dictionary = self.get_database_connection(connection_parameters["host"],
                                                                connection_parameters["user"],
                                                                connection_parameters["database"],
                                                                connection_parameters["port"])

        # If the connection is really a connection and not an error, proceed.
        if isinstance(connection_in_dictionary, psycopg2.extensions.connection):
            # Close and remove the current connection, because the connection should be reestablished. This is realized
            # by a re-connect.
            if self.close_and_remove_database_connection(connection_in_dictionary):
                # Re-connect with the given connection parameters.
                new_database_connection = self.get_database_connection(connection_parameters["host"],
                                                                       connection_parameters["user"],
                                                                       connection_parameters["database"],
                                                                       connection_parameters["port"])

                # Return the fresh and new database connection.
                return new_database_connection


global_connection_factory = ConnectionFactory()
