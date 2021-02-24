import logging

from PyQt5.QtWidgets import QFileDialog, QMessageBox

from pygadmin.database_query_executor import DatabaseQueryExecutor
from pygadmin.connectionfactory import global_connection_factory


class CSVExporter:
    """
    Create a class for exporting the current results to a CSV file. TODO: Docu
    """

    def __init__(self, parent, data_list, database_connection_parameters=None, table_name=None):
        """
        Get the parent for assigning the file dialog to a widget and the data list for the data, which will be saved.
        """

        # If the data list is None and the database connection parameters are None, there is no way to get the required
        # data for the csv file.
        if data_list is None and database_connection_parameters is None:
            # Show the error to the user and end the initialization.
            QMessageBox.critical(parent, "Data Error", "A data source for exporting to CSV is not given.")
            return

        # Define the parent, the data list and the file name as attributes.
        self.parent = parent
        self.data_list = data_list
        self.file_name = None

        # If the data list is None, the required data needs to be collected.
        if self.data_list is None:
            # Prepare the data list with building the query and preparing the database query executor.
            self.prepare_data_list(database_connection_parameters, table_name)
            # Set the success attribute to False, because the csv export is still in process and not successful at this
            # point in the program.
            self.success = False

    def prepare_data_list(self, database_connection_parameters, table_name):
        """
        Prepare the relevant parts for getting the data list with the database connection, the database query executor
        and the database query.
        """

        database_connection = self.get_database_connection(database_connection_parameters)

        if database_connection is None:
            return

        query = "SELECT * FROM {};".format(table_name)

        self.database_query_executor = DatabaseQueryExecutor()
        self.database_query_executor.result_data.connect(self.get_result_data_list)
        self.database_query_executor.database_connection = database_connection
        self.database_query_executor.database_query = query

    def get_database_connection(self, database_connection_parameters):
        database_connection = global_connection_factory.get_database_connection(database_connection_parameters["host"],
                                                                                database_connection_parameters["user"],
                                                                                database_connection_parameters[
                                                                                    "database"],
                                                                                database_connection_parameters["port"])

        if database_connection is None or database_connection is False:
            QMessageBox.critical(self.parent, "Database Connection Fail", "The connection to the database failed, "
                                                                          "please check the log for further "
                                                                          "information.")

            return None

        return database_connection

    def get_result_data_list(self, data_list):
        if data_list:
            self.data_list = data_list
            self.success = True
            self.export_and_save_csv_data()

    def get_file_name_by_file_dialog(self):
        """
        Create a file dialog for activating the csv export.
        """

        # Get a csv file with the default name result.csv and the file type csv.
        file_dialog_with_name_and_type = QFileDialog.getSaveFileName(self.parent, "Save File", "result.csv",
                                                                     "CSV (*.csv)")

        # Get the file name.
        file_name = file_dialog_with_name_and_type[0]

        # If the file name is not an empty string, return the file name, because in this case, the user has entered one.
        if file_name != "":
            return file_name

        # Inform the user in the log about the abort.
        else:
            logging.info("The current file saving process was aborted by the user, so the current result as csv file"
                         " is not saved.")

            # Return False, because there is no file name.
            return False

    def export_result_to_csv(self, file_name):
        """
        Export the result data to csv with the file name. Get the data out of the table model.
        """

        # Open the given file in write mode.
        with open(file_name, "w") as file_to_save:
            # Get through every data row in the data list.
            for data_row in self.data_list:
                # Get through every value in the data row.
                for data_value_counter in range(len(data_row)):
                    # Write every value.
                    file_to_save.write(str(data_row[data_value_counter]))

                    # If the value is not the last one, append a comma for comma separated value.
                    if data_value_counter != len(data_row) - 1:
                        file_to_save.write(",")

                # Write a newline at the end of a data row.
                file_to_save.write("\n")

    def export_and_save_csv_data(self):
        """
        Activate the export and save of the csv data.
        """

        if self.file_name is None:
            # Get the file name with a file dialog.
            self.file_name = self.get_file_name_by_file_dialog()

        # If the file name is False, the process of saving the file has been aborted.
        if self.file_name is False:
            # End the function with a return.
            return

        if self.data_list is None:
            self.database_query_executor.submit_and_execute_query()
            return

        # Save the current query result data.
        self.export_result_to_csv(self.file_name)

        return True
