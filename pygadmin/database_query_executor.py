import psycopg2
import logging

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool

from pygadmin.configurator import global_app_configurator
from pygadmin.connectionfactory import global_connection_factory


class QueryWorkerSignals(QObject):
    """
    Define a class of signals for QueryWorker, because QRunnable is not a QObject and cannot be used with own,
    customized signals.
    """

    # Define a signal for the result data in a list, which can be used by the table model.
    result_data = pyqtSignal(list)
    # Define a signal for a potential error. It contains a tuple of strings for the error title and the error message.
    error = pyqtSignal(tuple)
    # Define a signal for the query status message, which is processed in different ways.
    query_status_message = pyqtSignal(str)


class QueryWorker(QRunnable):
    """
    Define a query worker as QRunnable for executing a query as own thread with help of the thread pool. This makes
    other GUI operations, like showing the current status of query execution, possible.
    """

    def __init__(self, function_to_execute, query_text, database_cursor, parameter):
        """
        Get the function for executing, the text of the query and the database cursor for executing of the function with
        its parameters. Use also the signals of the class QueryWorkerSignals.
        """

        super().__init__()
        # Define the function for executing.
        self.function_to_execute = function_to_execute
        # Define the text of the query.
        self.query_text = query_text
        # Define the database cursor.
        self.database_cursor = database_cursor
        # Define the database query parameter.
        self.parameter = parameter
        # Get the signals with the helper class.
        self.signals = QueryWorkerSignals()

    @pyqtSlot()
    def run(self):
        """
        Define the function for running the relevant task, in this case executing the query. Try to run the function
        and define the workarounds for corner cases and exceptions. Emit the results with the signals.
        """

        # Define the result data list as empty list, which is used for errors.
        result_data_list = []
        # Define a query status message as None.
        query_status_message = None

        # Try to execute the query with the given function.
        try:
            # Get the result of the function.
            result = self.function_to_execute(self.query_text, self.database_cursor, self.parameter)
            # The first parameter is the data list.
            result_data_list = result[0]
            # The second parameter is the query status message.
            query_status_message = result[1]

        # At this point, the exception is mostly an SQL error, so an error is submitted.
        except Exception as sql_error:
            # Emit an error with the title and the description.
            self.signals.error.emit(("SQL Error", str(sql_error)))

        # In the end, emit all relevant signals.
        finally:
            # Emit the result data list.
            self.signals.result_data.emit(result_data_list)
            # Emit the query status message.
            self.signals.query_status_message.emit(query_status_message)


class DatabaseQueryExecutor(QObject):
    """
    Create a class for executing database queries, which is a child of QObject for the usage of slots and signals.
    """

    # Define a signal for the result data in a list, which can be used by the table model.
    result_data = pyqtSignal(list)
    # Define a signal for a potential error. It contains a tuple of strings for the error title and the error message.
    error = pyqtSignal(tuple)
    # Define a signal for the query status message, which is processed in different ways.
    query_status_message = pyqtSignal(str)
    # Define a signal for a refresh in the database connection. The database connection is for a failed connection a
    # boolean, so the possible types of the objects are bool and psycopg2.extensions.connection, so object is chosen for
    # the signal.
    new_database_connection = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        # Define the database connection, the database query and the database parameter as None for further usage and
        # overwrite.
        self.database_connection = None
        self.database_query = None
        self.database_query_parameter = None
        # Define a thread pool for the usage of different threads.
        self.thread_pool = QThreadPool()

    def submit_and_execute_query(self):
        """
        Check the connection for its validity and execute the query with the function for executing the query with a
        thread.
        """

        # Check the current database connection for its validity. This if-branch is used for an invalid connection.
        if self.check_for_valid_connection_and_reestablish() is False:
            # Emit an empty data list as error.
            self.result_data.emit([])
            # Emit an error to the user in a tuple.
            self.error.emit(("Connection Error", "The current database connection is invalid and cannot be used. "
                                                 "Further information can be found in the log. This error occurs "
                                                 "normally for a failed connection to the database server, which "
                                                 "occurred during the usage of pygadmin."))
            # End the function with a return.
            return

        # Create a query worker with the function for executing, the text of the query for executing and the relevant
        # database cursor.
        query_worker = QueryWorker(self.execute_query, self.database_query, self.database_connection.cursor(),
                                   self.database_query_parameter)
        # Connection the signal for the resulting data with the function for refreshing the table model with the fresh,
        # new data.
        query_worker.signals.result_data.connect(self.emit_result_data)
        # Connect a potential error to the function for error processing. The parameter of the title and the text as
        # tuple are used.
        query_worker.signals.error.connect(self.emit_error)
        # Connect the signal for the query status message to the function for checking and processing this message.
        query_worker.signals.query_status_message.connect(self.emit_query_status_message)
        # Start the thread.
        self.thread_pool.start(query_worker)

    @staticmethod
    def execute_query(query_to_execute, given_database_cursor, parameter=None):
        """
        Define a static method for executing the query. Use a query and a database cursor for processing. This method is
        static, because it is used in a separate thread. An explicit check for errors or try-except statements are not
        used, because the wrapper thread function is used for this kind of error handling with its signals.
        """

        # Use the given database cursor.
        with given_database_cursor as database_cursor:
            # Execute the determined query.
            database_cursor.execute(query_to_execute, parameter)
            # Get the status message of the query for further usage.
            query_status_message = database_cursor.statusmessage

            # If the cursor has a description, there is a data output, for example after a select statement with
            # existing tables and table data.
            if database_cursor.description:
                # Store the data result for the header/column data in a list.
                query_result_data_list = [[description[0] for description in database_cursor.description]]
                # Get all the plain result data.
                database_query_output = database_cursor.fetchall()

                # Iterate over every element in the output list and append every element/row of the result data to the
                # general result list to combine column data and row data.
                for result_element in database_query_output:
                    query_result_data_list.append(result_element)

            # If the description of the database cursor is not given, this is mostly the result of a database query
            # without a data request like an INSERT or a CREATE statement.
            else:
                query_success = "Query successful: {}".format(query_status_message)
                # Communicate the success of such a query without data result.
                query_result_data_list = [["Status"], (query_success,)]

        # Return the result data list and the query status message for further usage.
        return query_result_data_list, query_status_message

    def cancel_current_query(self):
        """
        Cancel the current query.
        """

        # Use the function for cancelling the current operation/query of a database connection. If there is not a
        # current query, nothing happens.
        self.database_connection.cancel()

    def check_for_valid_connection_and_reestablish(self):
        """
        Check for a currently valid database connection and reestablish a new one for an error.
        """

        # Check for a valid connection with the class function for checking.
        valid_connection = self.is_connection_valid()

        # If the connection is valid, everything is okay and nothing else is necessary.
        if valid_connection:
            # Return True for a success and a valid, functional connection.
            return True

        # Reestablish the connection with the given
        self.reestablish_connection()

        # Check, if the new connection is really a psycopg2 database connection. The database connection could also
        # be a boolean for a failed connection. The connection can also be closed or broken, so there is a check for a
        # closed database connection.
        if isinstance(self.database_connection, psycopg2.extensions.connection) \
                and self.database_connection.closed == 0:
            # Return True for a valid connection.
            return True

        # Return False, if the previous statements do not lead to a valid and functional connection. In this case, a
        # connection cannot be reestablished.
        return False

    def reestablish_connection(self):
        """
        Use a function for reestablishing the database connection.
        """

        database_parameter_dictionary = global_connection_factory.get_database_connection_parameters(
            self.database_connection)

        # Check, if the dictionary for the connection is not None. If there is no match for the database connection in
        # the connection factory, the database parameter dictionary is None.
        if database_parameter_dictionary is not None:
            # Get the current timeout time.
            timeout_time = global_app_configurator.get_single_configuration("Timeout")

            # If the timeout time is None, a configuration is not set and 10000 is used.
            if timeout_time is None:
                timeout_time = 10000

            # Add the timeout to the parameter dictionary.
            database_parameter_dictionary["timeout"] = timeout_time

            # Get a new database connection with the try of reestablishing the latest valid database connection.
            self.database_connection = global_connection_factory.reestablish_terminated_connection(
                database_parameter_dictionary)

            # Emit the new database connection.
            self.new_database_connection.emit(self.database_connection)

    def is_connection_valid(self):
        """
        Check for a valid connection. A connection is valid, if the variable, which should contain a connection,
        contains a connection. It can also contain "False" or "None" for an invalid connection. If the connection is
        also open, it is a valid connection.
        """

        # Check, if the variable for a connection really contains a psycopg2 connection.
        if isinstance(self.database_connection, psycopg2.extensions.connection):
            # Check for an open connection. If .closed is 0, the connection is open. If .closed is 1, the connection is
            # closed. The attribute works only for a connection, which is closed by Python.
            if self.database_connection.closed == 0:
                # Check, if the connection is really open or closed by the PostgreSQL server.
                try:
                    # Use the cursor of the database connection.
                    with self.database_connection.cursor() as database_cursor:
                        # Execute a test query. If the test query passes, the connection is valid.
                        database_cursor.execute("SELECT 42;")

                        # Return True for a valid connection.
                        return True

                # Use an exception for the connection error.
                except Exception as connection_error:
                    # Write a message about the error in the log.
                    logging.error("The current connection is not valid and produces the following error: {}".format(
                        connection_error), exc_info=True)

        # Return False as default, because if the method reaches this point, the connection is invalid.
        return False

    @pyqtSlot(list)
    def emit_result_data(self, result_data):
        """
        Emit the result data list. This function is used for a transfer.
        """

        self.result_data.emit(result_data)

    @pyqtSlot(tuple)
    def emit_error(self, error):
        """
        Emit the error. This function is used for a transfer.
        """

        self.error.emit(error)

    @pyqtSlot(str)
    def emit_query_status_message(self, query_status_message):
        """
        Emit the query status message. This function is used for a transfer.
        """

        self.query_status_message.emit(query_status_message)
